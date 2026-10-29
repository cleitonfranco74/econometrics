// Recursos visuais comuns a todas as páginas: números das seções,
// destaque do item atual no sumário e rótulo do botão de tema.
document.addEventListener('DOMContentLoaded',function(){
  // "4. Título" -> <span class="n">4</span> Título
  document.querySelectorAll('main h2').forEach(function(h){
    var t=h.firstChild;
    if(t&&t.nodeType===3){var m=t.nodeValue.match(/^\s*(\d+)\.\s+/);
      if(m){t.nodeValue=t.nodeValue.slice(m[0].length);var s=document.createElement('span');s.className='n';s.textContent=m[1];h.insertBefore(s,h.firstChild);}}
  });
  // Sumário: destaca a seção visível
  var links={}; document.querySelectorAll('nav.toc a[href^="#"]').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
  var ids=Object.keys(links);
  if(ids.length&&'IntersectionObserver' in window){
    var visiveis={};
    var obs=new IntersectionObserver(function(es){
      es.forEach(function(e){visiveis[e.target.id]=e.isIntersecting;});
      var atual=ids.filter(function(id){return visiveis[id];})[0];
      if(atual){ids.forEach(function(id){links[id].classList.toggle('ativo',id===atual);});}
    },{rootMargin:'-15% 0px -70% 0px'});
    ids.forEach(function(id){var el=document.getElementById(id); if(el) obs.observe(el);});
  }
  // Botão de tema com rótulo legível
  var btn=document.getElementById('themeBtn'), root=document.documentElement;
  function rotulo(){ if(!btn) return;
    var escuro=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&window.matchMedia('(prefers-color-scheme: dark)').matches);
    btn.textContent=escuro?'Modo claro':'Modo escuro'; }
  rotulo(); new MutationObserver(rotulo).observe(root,{attributes:true,attributeFilter:['data-theme']});
});
