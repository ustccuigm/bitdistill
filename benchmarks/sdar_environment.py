"""Single-task adapters using the upstream prompts, transitions, and rewards.

Runtime dependencies are imported from SDAR_ROOT; no upstream source is
copied here. Snapshots contain writable state, never a sequence of actions
to replay. Immutable corpora, search indexes, and game definitions stay shared.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import sys

_WEB_SERVERS = {}
_PLANNERS = []
_AVAILABLE_PLANNERS = []


def acquire_planner():
    import fast_downward
    if _AVAILABLE_PLANNERS:
        return _AVAILABLE_PLANNERS.pop()
    library = fast_downward.load_lib()
    # Planner plugins hold process-lifetime C++ registry references. Unloading
    # individual copies can leave dangling callbacks at interpreter shutdown.
    _PLANNERS.append(library)
    return library


def configure():
    root = Path(os.environ["SDAR_ROOT"])
    sys.path.insert(0, str(root))
    return root


def state_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def sas_at_facts(sas, positive_facts):
    """Replace SAS initial variable values with a captured logical state."""
    lines = sas.splitlines()
    values = []
    for index, line in enumerate(lines):
        if line != "begin_variable":
            continue
        count = int(lines[index + 3])
        domain = lines[index + 4:index + 4 + count]
        selected = [i for i, atom in enumerate(domain)
                    if atom.startswith("Atom ") and atom[5:] in positive_facts]
        if not selected:
            selected = [i for i, atom in enumerate(domain)
                        if atom.startswith("NegatedAtom ") and atom[12:] not in positive_facts]
        if not selected:
            selected = [i for i, atom in enumerate(domain) if atom == "<none of those>"]
        if len(selected) != 1:
            raise ValueError(f"Cannot restore SAS variable {lines[index + 1]}: {selected}")
        values.append(str(selected[0]))
    start, end = lines.index("begin_state"), lines.index("end_state")
    if end - start - 1 != len(values):
        raise ValueError("SAS state dimensions changed")
    return "\n".join(lines[:start + 1] + values + lines[end:]) + "\n"


class Environment:
    def __init__(self, benchmark, task, max_steps=None):
        self.root = configure()
        self.benchmark = benchmark
        self.task = task
        self.max_steps = max_steps or {"webshop": 15, "alfworld": 50, "search_qa": 4}[benchmark]
        self.turn = 0
        self.history = []
        self.done = self.success = False
        self.score = 0.
        self.last_action = ""
        if benchmark == "webshop":
            self._webshop_init()
        elif benchmark == "alfworld":
            self._alfworld_init()
        elif benchmark == "search_qa":
            self._search_init()
        else:
            raise ValueError(benchmark)

    def _webshop_init(self):
        root = self.root / "agent_system/environments/env_package/webshop/webshop"
        sys.path.insert(0, str(root))
        from web_agent_site.envs.web_agent_text_env import WebAgentTextEnv
        server_key = str(root)
        self.env = WebAgentTextEnv(
            observation_mode="text", num_products=1000, human_goals=False,
            file_path=str(root / "data/items_shuffle_1000.json"),
            attr_path=str(root / "data/items_ins_v2_1000.json"), seed=int(self.task.get("seed", 42)),
            server=_WEB_SERVERS.get(server_key),
        )
        _WEB_SERVERS[server_key] = self.env.server
        self.observation, _ = self.env.reset(session=int(self.task["task_id"]))
        self.description = self.env.get_instruction_text()

    def _alfworld_init(self):
        import textworld
        from textworld.envs.pddl.pddl import PddlEnv
        from agent_system.environments.env_package.alfworld.alfworld.agents.environment.alfred_tw_env import AlfredDemangler

        class ReusablePddlEnv(PddlEnv):
            def __init__(env, infos):
                textworld.Environment.__init__(env, infos)
                env.downward_lib = acquire_planner()

        self.base = ReusablePddlEnv(textworld.EnvInfos(won=True, admissible_commands=True, facts=True))
        self.env = AlfredDemangler(self.base, shuffle=False)
        self.env.load(self.task["gamefile"])
        state = self.env.reset()
        self.observation = state.feedback
        self.description = state.feedback.split("Your task is to: ", 1)[-1].strip()

    def _search_init(self):
        from omegaconf import OmegaConf
        from agent_system.environments.env_package.search.third_party.skyrl_gym.envs.search.env import SearchEnv
        from agent_system.environments.env_package.search.third_party.skyrl_gym.tools.search import call_search_api, _passages2string

        class CheckedSearchEnv(SearchEnv):
            def _execute_tool(env, group, name, queries):
                query = queries[0]
                if query is None:
                    return None
                response, error = call_search_api(
                    env.tool_group.search_url, query.strip(), topk=env.tool_group.topk,
                    timeout=env.tool_group.timeout, log_requests=False,
                    session=env.tool_group.session,
                )
                if error or not isinstance(response, dict) or "result" not in response:
                    env.retrieval_error = error or "invalid retrieval response"
                    raise RuntimeError(env.retrieval_error)
                try:
                    results = response["result"]
                    text = "\n---\n".join(_passages2string(row) for row in results) if results else "No search results found."
                except (TypeError, KeyError) as error:
                    env.retrieval_error = str(error)
                    raise
                return "\n<information>" + json.dumps({"result": text}) + "</information>\n"

            def step(env, action):
                env.retrieval_error = None
                result = super().step(action)
                # The upstream environment converts tool exceptions into
                # observations. Infrastructure failures must stop the run.
                if env.retrieval_error:
                    raise RuntimeError(f"Retriever infrastructure failure: {env.retrieval_error}")
                return result

        self.env = CheckedSearchEnv(OmegaConf.create({
            "search_url": os.environ.get("SEARCH_RETRIEVER_URL", "http://127.0.0.1:8000/retrieve"),
            "topk": 3, "timeout": 300, "log_requests": False,
        }))
        self.env.reset({"ground_truth": self.task["ground_truth"], "max_turns": self.max_steps,
                        "data_source": self.task["data_source"]})
        self.description = self.task["question"]
        self.observation = self.description

    def prompt(self):
        from agent_system.environments.prompts import (
            ALFWORLD_TEMPLATE, ALFWORLD_TEMPLATE_NO_HIS,
            WEBSHOP_TEMPLATE, WEBSHOP_TEMPLATE_NO_HIS,
            SEARCH_TEMPLATE, SEARCH_TEMPLATE_NO_HIS,
        )
        from agent_system.memory import SimpleMemory, SearchMemory
        memory = SearchMemory() if self.benchmark == "search_qa" else SimpleMemory()
        memory.reset(batch_size=1)
        for row in self.history:
            if self.benchmark == "search_qa":
                memory.store({"search": [row["response"]], "information": [row["after"]]})
            else:
                observation = self._format_web_observation(row["before"]) if self.benchmark == "webshop" else row["before"]
                memory.store({"text_obs": [observation], "action": [row["response"]]})
        if self.benchmark == "search_qa":
            if not self.history:
                return SEARCH_TEMPLATE_NO_HIS.format(task_description=self.description)
            context, _ = memory.fetch(len(self.history), obs_key="information", action_key="search")
            return SEARCH_TEMPLATE.format(task_description=self.description, memory_context=context[0], step_count=len(self.history))
        context, lengths = memory.fetch(len(self.history), obs_key="text_obs", action_key="action") if self.history else ([""], [0])
        fields = dict(task_description=self.description, current_observation=self.observation,
                      step_count=len(self.history), current_step=len(self.history) + 1,
                      history_length=lengths[0], action_history=context[0])
        if self.benchmark == "alfworld":
            fields["admissible_actions"] = "\n ".join(repr(action) for action in self.base.state.admissible_commands if action != "help")
            template = ALFWORLD_TEMPLATE if self.history else ALFWORLD_TEMPLATE_NO_HIS
        else:
            available = self.env.get_available_actions()
            actions = (["search[<your query>]"] if available["has_search_bar"] else [])
            actions += [f"click[{text}]" for text in available["clickables"]]
            fields["available_actions"] = "\n".join(f"'{action}'," for action in actions)
            # Match the upstream manager's removal of the repeated task header.
            fields["current_observation"] = self._format_web_observation(self.observation)
            template = WEBSHOP_TEMPLATE if self.history else WEBSHOP_TEMPLATE_NO_HIS
        return template.format(**fields)

    def _format_web_observation(self, observation):
        parts = observation.split(" [SEP] ")
        if self.description in parts:
            return " [SEP] ".join(repr(part) for part in parts[parts.index(self.description) + 1:])
        return observation

    def step(self, response):
        before = self.observation
        self.turn += 1
        if self.benchmark == "webshop":
            from agent_system.environments.env_package.webshop.projection import webshop_projection
            actions, valids = webshop_projection([response])
            action = actions[0]
            self.observation, self.score, done, _ = self.env.step(action)
            self.success = bool(done and self.score == 1.)
            valid = bool(valids[0])
        elif self.benchmark == "alfworld":
            from agent_system.environments.env_package.alfworld.projection import alfworld_projection
            actions, valids = alfworld_projection([response], [self.base.state.admissible_commands])
            action = actions[0]
            state, self.score, done = self.env.step(action)
            self.observation = state.feedback
            self.success = bool(state.won)
            valid = bool(valids[0])
        else:
            from agent_system.environments.env_package.search.projection import search_projection
            actions, valids = search_projection([response])
            action = actions[0]
            result = self.env.step(action)
            self.observation = "\n".join(row["content"] for row in result["observations"])
            self.score, done = result["reward"], result["done"]
            self.success = bool(done and self.score >= 1.)
            valid = bool(valids[0])
        self.done = bool(done or self.turn >= self.max_steps)
        self.last_action = action
        self.history.append({"before": before, "after": self.observation, "action": action, "response": response})
        return {"action": action, "observation": self.observation, "valid": valid,
                "done": self.done, "success": self.success, "score": float(self.score),
                "state_hash": state_hash(self.transition_state())}

    def transition_state(self):
        """Task effects exclude retry counts, query wording and browsing logs."""
        if self.benchmark == "alfworld":
            return {"facts": sorted(str(fact) for fact in self.base._pddl_state.facts),
                    "native": self._native_atoms(), "won": bool(self.base.state.won),
                    "observation": " ".join(str(self.observation).split()),
                    "commands": sorted(self.base.state.admissible_commands)}
        if self.benchmark == "webshop":
            session = self.env.server.user_sessions[self.env.session]
            return {"selection": {key: session.get(key) for key in
                    ("goal", "asin", "options", "page", "done", "reward")},
                    "observation": self._format_web_observation(self.observation)}
        evidence = sorted({" ".join(str(row["content"]).split())
                           for row in self.env.chat_history if row["role"] != "assistant"})
        return {"evidence": evidence, "done": self.env.done, "success": self.success}

    def semantic_hash(self):
        if self.benchmark == "alfworld":
            state = {"facts": sorted(str(fact) for fact in self.base._pddl_state.facts),
                     "native": self._native_atoms(),
                     "commands": self.base.state.admissible_commands,
                     "won": bool(self.base.state.won)}
        elif self.benchmark == "webshop":
            state = {"session": self.env.server.user_sessions[self.env.session], "url": self.env.browser.current_url,
                     "observation": self.observation, "success": self.success}
        else:
            # Reasoning wording is policy history, not an environmental effect.
            import re
            actions = []
            for row in self.env.chat_history:
                text = row["content"]
                if row["role"] == "assistant":
                    tags = re.findall(r"<(search|answer)>(.*?)</\1>", text, re.S)
                    actions.append(tags)
                else:
                    actions.append(text)
            state = {"history": actions, "done": self.env.done, "turns": self.env.turns}
        return state_hash(state)

    def _native_atoms(self):
        from fast_downward import Atom
        atoms = (Atom * self.base.downward_lib.get_state_size())()
        self.base.downward_lib.get_state(atoms)
        return sorted(atom.name for atom in atoms)

    def snapshot(self):
        import numpy as np
        state = {key: copy.deepcopy(getattr(self, key)) for key in
                 ("turn", "history", "done", "success", "score", "last_action", "observation", "description")}
        state.update(python_random=random.getstate(), numpy_random=np.random.get_state(),
                     semantic_hash=self.semantic_hash(), transition_hash=state_hash(self.transition_state()))
        if self.benchmark == "webshop":
            state["native"] = {
                "env": {key: copy.deepcopy(getattr(self.env, key)) for key in ("session", "instruction_text", "prev_obs", "prev_actions")},
                "browser": {key: copy.deepcopy(getattr(self.env.browser, key)) for key in ("current_url", "page_source", "session_id")},
                "session_state": copy.deepcopy(self.env.server.user_sessions[self.env.session]),
                "assigned_instruction_text": self.env.server.assigned_instruction_text,
            }
        elif self.benchmark == "search_qa":
            state["native"] = {key: copy.deepcopy(getattr(self.env, key)) for key in ("chat_history", "done", "turns")}
        else:
            facts = list(self.base._pddl_state.facts)
            # SAS atoms use untyped argument names; Proposition.__str__ adds
            # type annotations and cannot be used as the planner state key.
            positive = {f"{fact.name}({', '.join(arg.name for arg in fact.arguments)})"
                        for fact in facts if not fact.is_negation}
            state["native"] = {
                "sas": sas_at_facts(self.base._pddl_state.sas, positive),
                "sas_replan": sas_at_facts(self.base._pddl_state.sas_replan, positive),
                "facts": facts,
                "attributes": {key: copy.deepcopy(getattr(self.base, key)) for key in
                               ("_last_action", "_moves", "_entity_infos")},
                "state": copy.deepcopy(dict(self.base.state)),
                "prev_state": copy.deepcopy(dict(self.base.prev_state)) if self.base.prev_state is not None else None,
            }
        return state

    def restore(self, state):
        import numpy as np
        state = copy.deepcopy(state)
        native = state.pop("native")
        expected = state.pop("semantic_hash")
        state.pop("transition_hash", None)
        random.setstate(state.pop("python_random"))
        np.random.set_state(state.pop("numpy_random"))
        for key, value in state.items():
            setattr(self, key, value)
        if self.benchmark == "webshop":
            self.env.server.user_sessions[native["env"]["session"]] = native["session_state"]
            self.env.server.assigned_instruction_text = native["assigned_instruction_text"]
            for key, value in native["env"].items():
                setattr(self.env, key, value)
            for key, value in native["browser"].items():
                setattr(self.env.browser, key, value)
            # DOM nodes are derived from the captured HTML. Deep-copying their
            # parent/sibling graph can recurse indefinitely on product pages.
            self.env.get_available_actions()
        elif self.benchmark == "search_qa":
            for key, value in native.items():
                setattr(self.env, key, value)
        else:
            import textworld
            logical = self.base._pddl_state
            self.base.downward_lib.cleanup()
            self.base.downward_lib.load_sas(native["sas"].encode())
            self.base.downward_lib.load_sas_replan(native["sas_replan"].encode())
            logical.remove_facts(list(logical.facts))
            logical.add_facts(native["facts"])
            for key, value in native["attributes"].items():
                setattr(self.base, key, value)
            self.base.state = textworld.GameState(native["state"])
            self.base.prev_state = textworld.GameState(native["prev_state"]) if native["prev_state"] is not None else None
            self.base._gather_infos()
        if self.semantic_hash() != expected:
            raise ValueError("Environment snapshot restore changed task state")

    def save_snapshot(self, path):
        path = Path(path)
        state = self.snapshot()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(state, protocol=5))
        return state

    def close(self):
        if self.benchmark == "alfworld":
            if self.base.downward_lib is not None:
                self.base.downward_lib.cleanup()
                _AVAILABLE_PLANNERS.append(self.base.downward_lib)
                self.base.downward_lib = None
            return
        if self.benchmark == "webshop":
            self.env.server.user_sessions.pop(self.env.session, None)
        if hasattr(self.env, "close"):
            self.env.close()
