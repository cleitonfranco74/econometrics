// Funções compartilhadas pelas páginas de Estatística/Econometria (Conteúdos 3+).
// Sem dependências externas: tema, KaTeX, abas, gráficos SVG, números aleatórios e MQO.

// ---------- Tema claro/escuro ----------
(function(){
  var root=document.documentElement;
  try{var t=localStorage.getItem('theme'); if(t) root.setAttribute('data-theme',t);}catch(e){}
  document.addEventListener('DOMContentLoaded',function(){
    var btn=document.getElementById('themeBtn'); if(!btn) return;
    btn.addEventListener('click',function(){
      var cur=root.getAttribute('data-theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
      var next=cur==='dark'?'light':'dark';
      root.setAttribute('data-theme',next);
      try{localStorage.setItem('theme',next);}catch(e){}
      document.dispatchEvent(new Event('themechange'));
    });
  });
})();

// ---------- KaTeX e abas de código ----------
document.addEventListener('DOMContentLoaded',function(){
  if(window.renderMathInElement){
    renderMathInElement(document.body,{delimiters:[
      {left:'$$',right:'$$',display:true},{left:'\\(',right:'\\)',display:false}],throwOnError:false});
  }
  document.querySelectorAll('[data-tabs]').forEach(function(box){
    var btns=box.querySelectorAll('[data-tab]'), panels=box.querySelectorAll('[data-panel]');
    btns.forEach(function(b){
      b.addEventListener('click',function(){
        btns.forEach(function(x){x.setAttribute('aria-selected',x===b?'true':'false');});
        panels.forEach(function(p){p.classList.toggle('active',p.dataset.panel===b.dataset.tab);});
      });
    });
  });
  // Mostra o valor atual ao lado de cada controle deslizante
  document.querySelectorAll('.controls input[type=range]').forEach(function(inp){
    var out=document.querySelector('output[for="'+inp.id+'"]');
    var upd=function(){ if(out) out.textContent=fmt(+inp.value, +inp.dataset.dec||0); };
    inp.addEventListener('input',upd); upd();
  });
});

// ---------- Utilidades ----------
function fmt(v,d){
  if(v===undefined||v===null||!isFinite(v)) return '—';
  d=d===undefined?3:d;
  return v.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
}
function css(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim();}
function mean(a){var s=0;for(var i=0;i<a.length;i++)s+=a[i];return s/a.length;}

// Gerador pseudoaleatório com semente (mulberry32) e normal padrão (Box-Muller)
function rng(seed){
  var a=seed>>>0;
  var u=function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);
    t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
  return {unif:u, norm:function(){var x=u()||1e-12,y=u();return Math.sqrt(-2*Math.log(x))*Math.cos(2*Math.PI*y);}};
}

// ---------- MQO: y = Xb + e (X já inclui a coluna de 1s, se desejado) ----------
function invert(M){
  var n=M.length, A=M.map(function(r,i){return r.concat(Array.from({length:n},function(_,j){return i===j?1:0;}));});
  for(var c=0;c<n;c++){
    var p=c; for(var r=c+1;r<n;r++) if(Math.abs(A[r][c])>Math.abs(A[p][c])) p=r;
    var t=A[c];A[c]=A[p];A[p]=t;
    var d=A[c][c]; if(Math.abs(d)<1e-12) return null;
    for(var j=0;j<2*n;j++) A[c][j]/=d;
    for(r=0;r<n;r++) if(r!==c){var f=A[r][c]; for(j=0;j<2*n;j++) A[r][j]-=f*A[c][j];}
  }
  return A.map(function(r){return r.slice(n);});
}
function ols(X,y,w){
  var n=y.length,k=X[0].length,XtX=[],Xty=[];
  w=w||null;
  for(var a=0;a<k;a++){XtX.push(new Array(k).fill(0));Xty.push(0);}
  for(var i=0;i<n;i++){var wi=w?w[i]:1;
    for(a=0;a<k;a++){Xty[a]+=wi*X[i][a]*y[i]; for(var b=0;b<k;b++) XtX[a][b]+=wi*X[i][a]*X[i][b];}}
  var inv=invert(XtX); if(!inv) return null;
  var beta=inv.map(function(r){return r.reduce(function(s,v,j){return s+v*Xty[j];},0);});
  var ybar=mean(y), sse=0, sst=0, res=[];
  for(i=0;i<n;i++){var f=0; for(a=0;a<k;a++) f+=X[i][a]*beta[a]; var e=y[i]-f; res.push(e); sse+=e*e; sst+=(y[i]-ybar)*(y[i]-ybar);}
  var s2=sse/(n-k);
  return {beta:beta,se:inv.map(function(r,j){return Math.sqrt(s2*r[j]);}),r2:1-sse/sst,resid:res,n:n,k:k,s:Math.sqrt(s2)};
}

// ---------- Gráficos SVG ----------
function svgEl(tag,attrs,text){
  var e=document.createElementNS('http://www.w3.org/2000/svg',tag);
  for(var k in attrs) e.setAttribute(k,attrs[k]);
  if(text!==undefined) e.textContent=text;
  return e;
}
function niceTicks(lo,hi,count){
  var span=hi-lo||1, step=Math.pow(10,Math.floor(Math.log10(span/count))), err=span/count/step;
  if(err>=7.5) step*=10; else if(err>=3.5) step*=5; else if(err>=1.5) step*=2;
  var ticks=[]; for(var v=Math.ceil(lo/step)*step; v<=hi+1e-9; v+=step) ticks.push(+v.toFixed(10));
  return ticks;
}
function tickLabel(v){
  var a=Math.abs(v);
  return fmt(v, a===0||a>=100||v%1===0?0:(a>=10?1:(Math.abs(v*10%1)<1e-9?1:2)));
}
// Cria um painel com eixos. opts: {W,H,xlim,ylim,xlabel,ylabel,ylabel2 (eixo direito),margin}
function plotFrame(svg,opts){
  svg.innerHTML='';
  var W=opts.W||560,H=opts.H||340,m=opts.margin||{l:52,r:14,t:12,b:42};
  svg.setAttribute('viewBox','0 0 '+W+' '+H);
  var x0=opts.xlim[0],x1=opts.xlim[1],y0=opts.ylim[0],y1=opts.ylim[1];
  var sx=function(v){return m.l+(v-x0)/(x1-x0)*(W-m.l-m.r);};
  var sy=function(v){return H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);};
  var border=css('--border');
  niceTicks(y0,y1,5).forEach(function(v){
    svg.appendChild(svgEl('line',{x1:m.l,x2:W-m.r,y1:sy(v),y2:sy(v),stroke:border,'stroke-width':1}));
    svg.appendChild(svgEl('text',{x:m.l-6,y:sy(v)+4,'text-anchor':'end'},(opts.yfmt||tickLabel)(v)));
  });
  (opts.xticks||niceTicks(x0,x1,6)).forEach(function(v){
    svg.appendChild(svgEl('line',{x1:sx(v),x2:sx(v),y1:H-m.b,y2:H-m.b+4,stroke:css('--muted'),'stroke-width':1}));
    svg.appendChild(svgEl('text',{x:sx(v),y:H-m.b+16,'text-anchor':'middle'},(opts.xfmt||tickLabel)(v)));
  });
  svg.appendChild(svgEl('line',{x1:m.l,x2:W-m.r,y1:H-m.b,y2:H-m.b,stroke:css('--muted'),'stroke-width':1}));
  if(opts.xlabel) svg.appendChild(svgEl('text',{x:(m.l+W-m.r)/2,y:H-6,'text-anchor':'middle'},opts.xlabel));
  var yc=(m.t+H-m.b)/2;
  if(opts.ylabel) svg.appendChild(svgEl('text',{x:12,y:yc,'text-anchor':'middle',transform:'rotate(-90 12 '+yc+')',style:opts.ylabelColor?'fill:'+opts.ylabelColor:''},opts.ylabel));
  if(opts.ylabel2) svg.appendChild(svgEl('text',{x:W-10,y:yc,'text-anchor':'middle',transform:'rotate(90 '+(W-10)+' '+yc+')',style:opts.ylabel2Color?'fill:'+opts.ylabel2Color:''},opts.ylabel2));
  return {sx:sx,sy:sy,W:W,H:H,m:m,svg:svg,
    clip:function(v){return Math.max(y0,Math.min(y1,v));}};
}
function plotPoints(f,xs,ys,color,r,opacity){
  var g=svgEl('g',{fill:color,'fill-opacity':opacity===undefined?0.55:opacity});
  for(var i=0;i<xs.length;i++) g.appendChild(svgEl('circle',{cx:f.sx(xs[i]),cy:f.sy(ys[i]),r:r||3}));
  f.svg.appendChild(g); return g;
}
function plotLine(f,xs,ys,color,width,dash){
  var d=''; for(var i=0;i<xs.length;i++){ if(!isFinite(ys[i])) continue; d+=(d?'L':'M')+f.sx(xs[i]).toFixed(1)+' '+f.sy(ys[i]).toFixed(1);}
  var p=svgEl('path',{d:d,fill:'none',stroke:color,'stroke-width':width||2,'stroke-linejoin':'round','stroke-linecap':'round'});
  if(dash) p.setAttribute('stroke-dasharray',dash);
  f.svg.appendChild(p); return p;
}
function plotVLine(f,x,color,dash,label){
  var l=svgEl('line',{x1:f.sx(x),x2:f.sx(x),y1:f.m.t,y2:f.H-f.m.b,stroke:color,'stroke-width':1.5});
  if(dash) l.setAttribute('stroke-dasharray',dash);
  f.svg.appendChild(l);
  if(label) f.svg.appendChild(svgEl('text',{x:f.sx(x)+4,y:f.m.t+12,style:'fill:'+color},label));
}
// Intervalo de confiança vertical com ponto (gráfico de coeficientes)
function plotCI(f,x,est,lo,hi,color){
  f.svg.appendChild(svgEl('line',{x1:f.sx(x),x2:f.sx(x),y1:f.sy(lo),y2:f.sy(hi),stroke:color,'stroke-width':2}));
  f.svg.appendChild(svgEl('circle',{cx:f.sx(x),cy:f.sy(est),r:4.5,fill:color}));
}

// ---------- Distribuição t, p-valores e postos (usados nos estudos de caso) ----------
function lnGamma(z){
  var c=[76.18009172947146,-86.50532032941677,24.01409824083091,-1.231739572450155,0.1208650973866179e-2,-0.5395239384953e-5];
  var x=z,y=z,t=x+5.5; t-=(x+0.5)*Math.log(t); var s=1.000000000190015;
  for(var j=0;j<6;j++) s+=c[j]/++y;
  return -t+Math.log(2.5066282746310005*s/x);
}
function betacf(a,b,x){
  var qab=a+b,qap=a+1,qam=a-1,c=1,d=1-qab*x/qap; if(Math.abs(d)<1e-30)d=1e-30; d=1/d; var h=d;
  for(var m=1;m<=200;m++){
    var m2=2*m,aa=m*(b-m)*x/((qam+m2)*(a+m2));
    d=1+aa*d; if(Math.abs(d)<1e-30)d=1e-30; c=1+aa/c; if(Math.abs(c)<1e-30)c=1e-30; d=1/d; h*=d*c;
    aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));
    d=1+aa*d; if(Math.abs(d)<1e-30)d=1e-30; c=1+aa/c; if(Math.abs(c)<1e-30)c=1e-30; d=1/d;
    var del=d*c; h*=del; if(Math.abs(del-1)<3e-12) break;
  }
  return h;
}
function betai(a,b,x){
  if(x<=0) return 0; if(x>=1) return 1;
  var bt=Math.exp(lnGamma(a+b)-lnGamma(a)-lnGamma(b)+a*Math.log(x)+b*Math.log(1-x));
  return x<(a+1)/(a+b+2)? bt*betacf(a,b,x)/a : 1-bt*betacf(b,a,1-x)/b;
}
// p-valor bilateral de uma estatística t com gl graus de liberdade
function pT(t,gl){ return betai(gl/2,0.5,gl/(gl+t*t)); }
// p-valor de uma estatística F(q, gl)
function pF(F,q,gl){ return betai(gl/2,q/2,gl/(gl+q*F)); }
function stars(p){ return p<0.01?'***':p<0.05?'**':p<0.1?'*':''; }
function fmtP(p){ return p<0.001?'&lt;0,001':fmt(p,3); }
function ranks(a){
  var idx=a.map(function(v,i){return [v,i];}).sort(function(x,y){return x[0]-y[0];}), r=new Array(a.length);
  for(var i=0;i<idx.length;){var j=i; while(j+1<idx.length&&idx[j+1][0]===idx[i][0]) j++;
    for(var k=i;k<=j;k++) r[idx[k][1]]=(i+j)/2+1; i=j+1;}
  return r;
}
function pearson(x,y){
  var mx=mean(x),my=mean(y),sxy=0,sx=0,sy=0;
  for(var i=0;i<x.length;i++){sxy+=(x[i]-mx)*(y[i]-my);sx+=(x[i]-mx)*(x[i]-mx);sy+=(y[i]-my)*(y[i]-my);}
  return sxy/Math.sqrt(sx*sy);
}
function statCards(id,items){
  document.getElementById(id).innerHTML=items.map(function(it){return '<div class="stat"><div class="k">'+it[0]+'</div><div class="v">'+it[1]+'</div></div>';}).join('');
}
