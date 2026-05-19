
// ── OTP / Verificación ──
async function sendOTP(email){
  if(!email){alert('Email requerido');return;}
  try{
    const r = await fetch('https://tengovisard.com/push/api.php?token=tgvsa&user_id=tengovisa%40gmail.com&title='+encodeURIComponent('Código OTP TengoVisa')+'&message='+encodeURIComponent('Tu código es: '+Math.floor(100000+Math.random()*900000)),{method:'GET'});
    alert('Código enviado a '+email);
  }catch(e){alert('Error enviando OTP: '+e.message);}
}
async function verifyOTP(code){
  alert('Verificando código: '+code);
}
/* TengoVisaRD Sidebar v5 - validado */
(function(){
  if(document.getElementById("tv-sb5"))return;

  /* CSS */
  var st=document.createElement("style");
  st.textContent=[
    "#tv-sb5{position:fixed;left:0;top:0;height:100vh;width:260px;background:#fff",
    ";border-right:3px solid #001F73;z-index:8000;transform:translateX(-100%)",
    ";transition:.25s;display:flex;flex-direction:column",
    ";box-shadow:4px 0 20px rgba(0,31,115,.15)}",
    "#tv-sb5.open{transform:translateX(0)}",
    "#tv-tog5{position:fixed;left:0;top:45%;transform:translateY(-50%)",
    ";background:#CC1A1A;color:#fff;border:none;padding:12px 6px;cursor:pointer",
    ";border-radius:0 10px 10px 0;font-size:18px;z-index:8001}",
    ".t5h{background:#001F73;color:#fff;padding:12px 14px;font-weight:800",
    ";font-size:13px;display:flex;justify-content:space-between;align-items:center",
    ";border-bottom:3px solid #CC1A1A;flex-shrink:0}",
    ".t5b{padding:10px;overflow-y:auto;flex:1}",
    ".t5s{font-size:9px;font-weight:800;color:#94A3B8;text-transform:uppercase",
    ";letter-spacing:.08em;margin:8px 0 3px;padding-bottom:3px",
    ";border-bottom:1px solid #F1F5F9}",
    ".t5n{width:100%;padding:9px 12px;border:none;border-radius:7px;font-size:11px",
    ";font-weight:700;cursor:pointer;text-align:left;margin-bottom:4px",
    ";display:block;font-family:inherit}",
    ".t5n:hover{opacity:.85}",
    ".t5del{background:#FEF2F2;border:1px solid #FECACA;color:#CC1A1A",
    ";border-radius:5px;padding:2px 7px;font-size:11px;cursor:pointer",
    ";margin-left:auto;font-weight:700;flex-shrink:0}",
    "#tv-ca{background:#EAF0FF;border:1px solid #C7D7F5;border-radius:8px",
    ";padding:8px 10px;margin-bottom:8px;font-size:11px;display:none}",
    "#tv-ca-nm{font-weight:800;color:#001F73;font-size:12px}"
  ].join("");
  document.head.appendChild(st);

  /* Toggle */
  var tog=document.createElement("button");
  tog.id="tv-tog5";
  tog.innerHTML="&#9776;";
  tog.title="Panel herramientas";
  tog.onclick=function(){document.getElementById("tv-sb5").classList.toggle("open");};
  document.body.appendChild(tog);

  /* Sidebar */
  var sb=document.createElement("div");
  sb.id="tv-sb5";

  var hdr=document.createElement("div");
  hdr.className="t5h";
  hdr.innerHTML="<span>Panel</span>";
  var cls=document.createElement("button");
  cls.style.cssText="background:none;border:none;color:#fff;cursor:pointer;font-size:18px";
  cls.textContent="x";
  cls.onclick=function(){document.getElementById("tv-sb5").classList.remove("open");};
  hdr.appendChild(cls);
  sb.appendChild(hdr);

  var body=document.createElement("div");
  body.className="t5b";

  /* Info caso activo */
  var caInfo=document.createElement("div");
  caInfo.id="tv-ca";
  caInfo.innerHTML='<div id="tv-ca-nm">-</div><div id="tv-ca-em" style="color:#64748B;font-size:10px">-</div>';
  body.appendChild(caInfo);

  /* Botones */
  function sec(txt){
    var d=document.createElement("div");
    d.className="t5s";
    d.textContent=txt;
    body.appendChild(d);
  }
  function btn(label,bg,color,fn){
    var b=document.createElement("button");
    b.className="t5n";
    b.style.background=bg;
    b.style.color=color;
    b.textContent=label;
    b.onclick=fn;
    body.appendChild(b);
  }

  sec("Caso activo");
  btn("Ver / Editar DS-160","#EAF0FF","#001F73",function(){tv5act(function(){openDS160(S.CID);});});
  btn("Auto-llenar DNA","#EAF8EE","#16A34A",function(){tv5act(function(){llenarDNA();});});
  btn("PDF Resumen","#FFF4DE","#B45309",function(){tv5act(function(){genPDF();});});
  btn("JSON CEAC","#F3E8FF","#7C3AED",function(){tv5act(function(){tv5Ceac();});});
  btn("Analisis IA","#001F73","#fff",function(){tv5act(function(){runIA();});});
  btn("Archivar caso","#FCEBEB","#CC1A1A",function(){tv5act(function(){confirmDel();});});

  sec("Nuevo");
  btn("Importar PDF","#CC1A1A","#fff",function(){tv5Pdf();});
  btn("Generar link cliente","#001F73","#fff",function(){if(typeof openM==="function")openM("m-link");});

  sec("Ir a");
  btn("Dashboard","#F5F7FA","#1A1A1A",function(){if(typeof setTab==="function")setTab("dash");});
  btn("DS-160","#F5F7FA","#1A1A1A",function(){if(typeof setTab==="function")setTab("ds160");});
  btn("Evaluaciones","#F5F7FA","#1A1A1A",function(){if(typeof setTab==="function")setTab("eval");});
  btn("Global Entry","#F5F7FA","#1A1A1A",function(){if(typeof setTab==="function")setTab("ge");});

  sb.appendChild(body);
  document.body.appendChild(sb);

  /* Actualizar info cuando se abre caso */
  document.addEventListener("click",function(e){
    var el=e.target.closest("[onclick]");
    if(!el)return;
    var oc=el.getAttribute("onclick")||"";
    if(oc.indexOf("openDS160")<0)return;
    setTimeout(function(){
      if(!window.S||!S.CID)return;
      var c=S.ds160&&S.ds160.find(function(x){return x.id===S.CID;});
      if(!c)return;
      caInfo.style.display="block";
      document.getElementById("tv-ca-nm").textContent=(c._nombre||"")+(c._apellido?" "+c._apellido:"");
      document.getElementById("tv-ca-em").textContent=(c._email||"")+" · "+(c._pct||0)+"% completo";
    },600);
  });

  /* Botón eliminar en listas */
  new MutationObserver(function(){
    document.querySelectorAll("#list-d .item,#list-e .item,#list-g .item").forEach(function(el){
      if(el.querySelector(".t5del"))return;
      var oc=el.getAttribute("onclick")||"";
      var m=oc.match(/openDS160\('([^']+)'\)/)||oc.match(/open(?:Eval|GE)\('([^']+)'\)/);
      if(!m)return;
      var id=m[1];
      var b=document.createElement("button");
      b.className="t5del";
      b.textContent="x";
      b.title="Archivar";
      b.onclick=function(e){
        e.stopPropagation();
        if(!confirm("Archivar este caso?"))return;
        fetch("/api/ds160/field/v2/"+id,{
          method:"POST",
          headers:{"Content-Type":"application/json","x-api-key":"TengoVisa2026API"},
          body:JSON.stringify({field:"estado",value:"archivado"})
        }).then(function(){if(typeof loadAll==="function")loadAll();});
      };
      el.style.display="flex";
      el.style.alignItems="center";
      el.appendChild(b);
    });
  }).observe(document.body,{childList:true,subtree:true});

  /* tv5act — ejecutar funcion si hay caso activo */
  window.tv5act=function(fn){
    var cid=(window.S&&S.CID)||null;
    if(cid){fn();return;}
    if(typeof toast==="function")toast("Haz clic en un cliente de la lista primero","err");
    else alert("Haz clic en un cliente de la lista DS-160 primero");
  };

  /* CEAC Export */
  window.tv5Ceac=async function(){
    if(!window.S||!S.CID)return;
    try{
      var r=await fetch("/api/ds160/ceac-json/"+S.CID,{headers:{"x-api-key":"TengoVisa2026API"}});
      var d=await r.json();
      if(!d.ok){alert("Error: "+(d.error||"?"));return;}
      var blob=new Blob([JSON.stringify(d.ceac,null,2)],{type:"application/json"});
      var url=URL.createObjectURL(blob);
      var a=document.createElement("a");
      var nm=(d.ceac._meta.nombre_completo||"caso").replace(/\s+/g,"_");
      a.href=url;
      a.download="CEAC_"+nm+"_"+new Date().toISOString().substring(0,10)+".json";
      a.click();
      setTimeout(function(){URL.revokeObjectURL(url);},3000);
      if(typeof toast==="function")toast("JSON CEAC descargado","ok");
    }catch(e){alert("Error: "+e.message);}
  };

  /* PDF Import */
  window.tv5Pdf=function(){
    var m=document.getElementById("tv5-pdf-modal");
    if(m){m.style.display="flex";return;}
    var modal=document.createElement("div");
    modal.id="tv5-pdf-modal";
    modal.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9000;display:flex;align-items:center;justify-content:center;padding:12px";
    var box=document.createElement("div");
    box.style.cssText="background:#fff;border-radius:14px;width:100%;max-width:420px;box-shadow:0 20px 60px rgba(0,0,0,.3)";
    var h2=document.createElement("div");
    h2.style.cssText="background:#001F73;color:#fff;padding:14px 16px;border-radius:14px 14px 0 0;border-bottom:3px solid #CC1A1A;display:flex;justify-content:space-between;align-items:center";
    h2.innerHTML="<div><div style=\"font-weight:800;font-size:14px\">Importar PDF</div><div style=\"font-size:9px;opacity:.7\">IA extrae datos del formulario DS-160</div></div>";
    var cls2=document.createElement("button");
    cls2.style.cssText="background:rgba(255,255,255,.2);border:none;color:#fff;padding:6px 10px;border-radius:6px;cursor:pointer";
    cls2.textContent="x";
    cls2.onclick=function(){modal.style.display="none";};
    h2.appendChild(cls2);
    box.appendChild(h2);
    var body2=document.createElement("div");
    body2.style.cssText="padding:16px;display:flex;flex-direction:column;gap:12px";
    var dropzone=document.createElement("div");
    dropzone.style.cssText="border:2px dashed #CBD5E1;border-radius:10px;padding:28px;text-align:center;cursor:pointer;background:#F8FAFC";
    dropzone.innerHTML="<div style=\"font-size:32px;margin-bottom:8px\">PDF</div><div style=\"color:#001F73;font-weight:800;font-size:13px\">Clic para subir PDF</div><div style=\"color:#94A3B8;font-size:11px;margin-top:3px\">Formulario evaluacion DS-160</div>";
    var inp=document.createElement("input");
    inp.type="file";inp.accept=".pdf";inp.style.display="none";
    inp.onchange=function(){tv5PdfProc(inp.files[0]);};
    dropzone.onclick=function(){inp.click();};
    dropzone.appendChild(inp);
    body2.appendChild(dropzone);
    var st2=document.createElement("div");
    st2.id="tv5-st";st2.style.display="none";
    st2.style.cssText="display:none;border-radius:8px;padding:10px 14px;font-size:12px;font-weight:700";
    body2.appendChild(st2);
    var pv=document.createElement("div");
    pv.id="tv5-pv";pv.style.display="none";
    pv.innerHTML="<div style=\"font-size:11px;font-weight:800;color:#001F73;margin-bottom:6px\">Campos extraidos:</div><div id=\"tv5-fl\" style=\"font-size:10px;max-height:160px;overflow-y:auto;border:1px solid #E2E8F0;border-radius:8px;padding:8px;background:#F8FAFC\"></div><div style=\"display:flex;gap:8px;margin-top:10px\"><button onclick=\"tv5PdfSave()\" style=\"flex:1;padding:10px;background:#001F73;color:#fff;border:none;border-radius:8px;font-size:12px;font-weight:800;cursor:pointer\">Crear Caso DS-160</button><button onclick=\"document.getElementById('tv5-pdf-modal').style.display='none'\" style=\"flex:1;padding:10px;background:#F1F5F9;color:#475569;border:none;border-radius:8px;font-size:12px;cursor:pointer\">Cancelar</button></div>";
    body2.appendChild(pv);
    box.appendChild(body2);
    modal.appendChild(box);
    document.body.appendChild(modal);
  };

  window._tv5pdf={};
  window.tv5PdfProc=async function(file){
    if(!file)return;
    var st=document.getElementById("tv5-st");
    var pv=document.getElementById("tv5-pv");
    st.style.display="block";st.style.background="#EFF6FF";st.style.color="#1D4ED8";
    st.textContent="Leyendo PDF con IA... (20-40 seg)";
    pv.style.display="none";
    try{
      var b64=await new Promise(function(res,rej){
        var r=new FileReader();
        r.onload=function(){res(r.result.split(",")[1]);};
        r.onerror=rej;
        r.readAsDataURL(file);
      });
      var resp=await fetch("/api/pdf/extract",{
        method:"POST",
        headers:{"Content-Type":"application/json","x-api-key":"TengoVisa2026API"},
        body:JSON.stringify({pdf_b64:b64,filename:file.name})
      });
      var d=await resp.json();
      if(d.datos&&Object.keys(d.datos).length>0){
        window._tv5pdf=d.datos;
        var arr=Object.entries(d.datos).filter(function(e){return e[1];});
        document.getElementById("tv5-fl").innerHTML=arr.map(function(e){
          return "<div style=\"padding:3px 0;border-bottom:1px solid #F1F5F9;display:flex;gap:8px\"><span style=\"color:#94A3B8;min-width:130px;font-size:9.5px;flex-shrink:0\">"+e[0].replace(/_/g," ")+"</span><span style=\"font-weight:700;font-size:10px\">"+String(e[1]).substring(0,40)+"</span></div>";
        }).join("");
        st.style.background="#F0FDF4";st.style.color="#15803D";
        st.textContent=arr.length+" campos extraidos";
        pv.style.display="block";
      }else{
        st.style.background="#FEF2F2";st.style.color="#CC1A1A";
        st.textContent="Sin datos. Verifica que sea PDF de evaluacion.";
      }
    }catch(e){
      st.style.background="#FEF2F2";st.style.color="#CC1A1A";
      st.textContent="Error: "+e.message;
    }
  };

  window.tv5PdfSave=async function(){
    if(!Object.keys(window._tv5pdf).length){alert("Sin datos");return;}
    try{
      var r=await fetch("/api/ds160/crear",{
        method:"POST",
        headers:{"Content-Type":"application/json","x-api-key":"TengoVisa2026API"},
        body:JSON.stringify({datos:window._tv5pdf,estado:"revision"})
      });
      var d=await r.json();
      if(d.ok||d.id){
        document.getElementById("tv5-pdf-modal").style.display="none";
        if(typeof loadAll==="function")loadAll();
        if(typeof toast==="function")toast("Caso creado","ok");
        else alert("Caso creado correctamente");
      }else alert("Error: "+(d.error||"?"));
    }catch(e){alert("Error: "+e.message);}
  };

})();
