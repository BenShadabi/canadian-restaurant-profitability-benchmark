/* Shared site navigation, scroll reveal and number count-up. Plain JavaScript, no libraries.
   Pages that already do their own reveal (they contain a .rv element) only get the navigation. */
(function(){
  var reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
  var here=location.pathname.split("/").pop()||"index.html";
  var links=[["index.html","Benchmark"],["dashboard.html","Dashboard"],["calculator.html","Compare yours"],["toronto.html","Toronto"]];
  var st=document.createElement("style");
  st.textContent="body{padding-top:48px}.sitenav{position:fixed;top:0;left:0;right:0;z-index:50;height:48px;background:rgba(11,32,56,.9);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.12)}"+
    ".sitenav div{max-width:1040px;margin:0 auto;padding:0 12px;height:100%;display:flex;align-items:center;gap:4px;overflow-x:auto;scrollbar-width:none}.sitenav b{color:#E3B965;font:650 .875rem/1 system-ui,sans-serif;letter-spacing:.04em;margin-right:auto;white-space:nowrap;padding:0 8px}"+
    ".sitenav a{color:#C9D8EA!important;text-decoration:none;font:600 .875rem/1 system-ui,sans-serif;padding:10px 12px;border-radius:999px;white-space:nowrap;transition:background .2s,color .2s}.sitenav a:hover{background:rgba(255,255,255,.1);color:#fff!important}.sitenav a[aria-current=page]{background:#E3B965;color:#0B2038!important}"+
    "@media(max-width:560px){.sitenav b{display:none}}";
  document.head.appendChild(st);
  var nav=document.createElement("nav");nav.className="sitenav";nav.setAttribute("aria-label","Site");
  nav.innerHTML="<div><b>RESTAURANT BENCHMARK</b>"+links.map(function(l){return '<a href="'+l[0]+'"'+(l[0]===here?' aria-current="page"':'')+'>'+l[1]+'</a>'}).join("")+"</div>";
  document.body.insertBefore(nav,document.body.firstChild);
  if(document.querySelector(".rv"))return;
  if(!reduce&&"IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("min");io.unobserve(e.target)}})},{threshold:.08});
    var els=[].slice.call(document.querySelectorAll("main h2, main .card, main figure, main .big > div, main .note, main table, main .chips li, main section"));
    var chosen=els.filter(function(el){return !el.parentElement.closest(".mrv")&&!el.closest("header")});
    chosen.forEach(function(el,i){el.classList.add("mrv");el.style.transitionDelay=Math.min((i%4)*70,210)+"ms";io.observe(el)});
    setTimeout(function(){chosen.forEach(function(el){if(el.getBoundingClientRect().top<innerHeight)el.classList.add("min")})},900);
    setTimeout(function(){chosen.forEach(function(el){el.classList.add("min")})},6000);
    document.querySelectorAll(".big b:not([id]), .chips li b").forEach(function(el){
      var m=el.textContent.trim().match(/^(\$?)([\d,]+(?:\.\d+)?)(%?)$/);if(!m)return;
      var end=parseFloat(m[2].replace(/,/g,"")),dec=(m[2].split(".")[1]||"").length,full=el.textContent;
      var o=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;o.disconnect();var t0=performance.now();
        (function f(t){var k=Math.min(1,(t-t0)/1200),v=end*(1-Math.pow(1-k,3));el.textContent=m[1]+(dec?v.toFixed(dec):Math.round(v).toLocaleString("en-CA"))+m[3];if(k<1)requestAnimationFrame(f);else el.textContent=full})(t0)})});
      o.observe(el);
    });
  }
})();
