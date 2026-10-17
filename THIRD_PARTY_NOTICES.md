# Third-Party Notices

This supplementary archive contains the method-specific glue and modified
training/quantization code. Large models, datasets, vLLM, and the tool-use environment
are external dependencies and are not bundled in the archive.

The following projects are used or referenced by the route. Their licenses
and citation requirements must be preserved when the corresponding external
source is downloaded.

| Component | License / notice | Source |
|---|---|---|
| BitDistiller base code | MIT; see upstream `LICENSE` | https://github.com/DD-DuDa/BitDistiller |
| Tool-use environment adapter | See upstream repository and dataset terms | https://github.com/Snowflake-Labs/agent-world-model |
| Tool-use trajectory dataset | See Hugging Face dataset card | https://huggingface.co/datasets/Snowflake/AgentWorldModel-1K |
| Qwen3-8B base model | See the Hugging Face model card and license | https://huggingface.co/Qwen/Qwen3-8B |
| Qwen3.5-4B base model | See the Hugging Face model card and license | https://huggingface.co/Qwen/Qwen3.5-4B |
| Gemma 4 12B-it base model | See the Hugging Face model card and Gemma license; weights are not redistributed | https://huggingface.co/google/gemma-4-12B-it |
| SDAR environment integrations | Preserve upstream licenses and embedded component notices | https://github.com/ZJU-REAL/SDAR |
| BFCL | Apache-2.0; upstream license and benchmark terms | https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard |
| tau2-bench | MIT; upstream license and data terms | https://github.com/sierra-research/tau2-bench |
| WebShop | Upstream code license and product-data terms | https://github.com/princeton-nlp/WebShop |
| ALFWorld / TextWorld | Upstream licenses and game-data terms | https://github.com/alfworld/alfworld |
| Search-R1 | Upstream license, source dataset terms, and retrieval corpus terms | https://github.com/PeterGriffinJin/Search-R1 |
| AutoAWQ reference | MIT; upstream `LICENSE` | https://github.com/casper-hansen/AutoAWQ |
| GPTQ-triton reference | Apache-2.0; full text in `licenses/GPTQ-triton-LICENSE` | https://github.com/fpgaminer/GPTQ-triton |
| Triton | See the installed package license | https://github.com/triton-lang/triton |
| vLLM | Apache-2.0; see the installed package license | https://github.com/vllm-project/vllm |
| Transformers | Apache-2.0; see the installed package license | https://github.com/huggingface/transformers |
| Flash Linear Attention | See the pinned package's upstream license | https://github.com/fla-org/flash-linear-attention |

The archive does not repackage the external repositories. A release that
redistributes any of those repositories or downloaded model/data files must
include their complete notices and comply with their individual terms.

The quantization kernels include adapted code attributed to Vedant Roy and
reference GPTQ-triton. Their original source notices are retained; the root
MIT license does not replace the Apache-2.0 terms for incorporated
GPTQ-triton material. Benchmark-specific data terms must be checked when
downloading assets; those data are not distributed in this source tree.
