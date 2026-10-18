document.querySelectorAll('video').forEach(video=>{
  video.addEventListener('play',()=>{
    document.querySelectorAll('video').forEach(other=>{if(other!==video)other.pause()});
  });
});
