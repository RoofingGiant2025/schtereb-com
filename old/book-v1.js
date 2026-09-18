(function(){
  var page=document.querySelector('main.page');
  if(!page) return;
  var prev=page.dataset.prev, next=page.dataset.next;
  function go(href){ if(href) location.href=href; }
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' ') { if(e.key===' '&&window.innerHeight+window.scrollY<document.body.scrollHeight-2) return; e.preventDefault(); go(next); }
    else if(e.key==='ArrowLeft'||e.key==='PageUp'){ e.preventDefault(); go(prev); }
    else if(e.key==='Escape'){ go('./'); }
  });
  var x0=null,y0=null;
  document.addEventListener('touchstart',function(e){ x0=e.touches[0].clientX; y0=e.touches[0].clientY; },{passive:true});
  document.addEventListener('touchend',function(e){
    if(x0===null) return; var dx=e.changedTouches[0].clientX-x0, dy=e.changedTouches[0].clientY-y0; x0=y0=null;
    if(Math.abs(dx)>70 && Math.abs(dy)<Math.abs(dx)*0.6){ go(dx<0?next:prev); }
  },{passive:true});
  // side-by-side with the original (remembered per browser)
  var btn=document.querySelector('.pager .side'), spread=document.querySelector('.spread'), orig=document.querySelector('.original');
  function setSide(on){
    if(!orig) return;
    orig.hidden=!on; spread.classList.toggle('side',on);
    if(btn){ btn.setAttribute('aria-pressed',on?'true':'false'); btn.textContent=on?btn.dataset.on:btn.dataset.off; }
    try{ localStorage.setItem('side',on?'1':'0'); }catch(e){}
  }
  var saved='0'; try{ saved=localStorage.getItem('side')||'0'; }catch(e){}
  if(orig) setSide(saved==='1');
  if(btn) btn.addEventListener('click',function(){ setSide(orig.hidden); });
  // prefetch neighbours
  [prev,next].forEach(function(h){ if(!h) return; var l=document.createElement('link'); l.rel='prefetch'; l.href=h; document.head.appendChild(l); });
})();
