(function(){
  if(document.getElementById('tvrd-panel'))return;

  const panel=document.createElement('div');
  panel.id='tvrd-panel';
  panel.style.cssText='position:fixed;bottom:0;right:0;width:295px;background:#001F73;color:#fff;font-family:Arial,sans-serif;font-size:12px;z-index:99999;border-radius:12px 0 0 0;box-shadow:-2px -2px 14px rgba(0,0,0,.4)';
  panel.innerHTML=`
    <div id="tvrd-hdr" style="padding:9px 13px;display:flex;align-items:center;justify-content:space-between;cursor:pointer;user-select:none">
      <span style="font-weight:700;font-size:13px">🛂 TengoVisaRD DS-160</span>
      <span id="tvrd-pg" style="font-size:10px;opacity:.75;margin:0 8px"></span>
      <span id="tvrd-tog" style="font-size:13px">▲</span>
    </div>
    <div id="tvrd-body" style="background:#fff;color:#0F172A;padding:10px 12px">
      <div id="tvrd-cli" style="font-size:11px;color:#475569;margin-bottom:7px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Sin datos — carga el JSON</div>
      <div id="tvrd-sta" style="font-size:11px;background:#EAF0FF;color:#001F73;padding:5px 9px;border-radius:7px;margin-bottom:8px;min-height:22px">Abre la extensión y carga el JSON</div>
      <div id="tvrd-pw" style="background:#E2E8F0;border-radius:10px;height:5px;margin-bottom:8px;display:none">
        <div id="tvrd-pr" style="height:100%;background:#001F73;width:0%;transition:width .4s;border-radius:10px"></div>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:7px">
        <button id="tvrd-btn" style="flex:1;padding:9px;background:#001F73;color:#fff;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;font-family:Arial;opacity:.5" disabled>▶ Llenar página</button>
        <button id="tvrd-next" style="padding:9px 12px;background:#16A34A;color:#fff;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;font-family:Arial">Next ›</button>
      </div>
      <button id="tvrd-auto" style="width:100%;padding:9px;background:#7C3AED;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;font-family:Arial">⚡ AUTO CEAC v2</button>
    </div>
  `;
  document.body.appendChild(panel);

  function detectPage(){
    const qs=window.location.search;
    const node=(qs.match(/[?&]node=([^&]+)/i)||[])[1]||'';
    const n=node.toLowerCase().replace(/\s/g,'');
    const MAP={
      'personal1':'P1','personal2':'P2',
      'address':'P3','addressandphone':'P3',
      'passport':'P4',
      'travel':'P5','travelinformation':'P5',
      'travelcompanions':'P6',
      'previousustravel':'P7','previoustravel':'P7','prevustravel':'P7',
      'poc':'P8','uscontact':'P8','pointofcontact':'P8','uspointofcontact':'P8',
      'family1':'P9A','family2':'P9B',
      'workeducation1':'P10','presentwork':'P10',
      'workeducation2':'P11','previousworkeducation':'P11',
      'workeducation3':'P12',
      'securityandbackground1':'P13','securitybackground1':'P13',
      'securityandbackground2':'P14','securitybackground2':'P14',
      'securityandbackground3':'P15','securitybackground3':'P15',
      'securityandbackground4':'P16','securitybackground4':'P16',
      'securityandbackground5':'P17','securitybackground5':'P17',
      'preparedby':'PFINAL','preparer':'PFINAL',
    };
    if(MAP[n]) return {page:MAP[n],node};
    const t=(document.title||'').toLowerCase();
    if(t.includes('personal 1')) return {page:'P1',node};
    if(t.includes('personal 2')) return {page:'P2',node};
    if(t.includes('address')) return {page:'P3',node};
    if(t.includes('passport')) return {page:'P4',node};
    if(t.includes('travel information')||t.includes('travel plan')) return {page:'P5',node};
    if(t.includes('companion')) return {page:'P6',node};
    if(t.includes('previous u.s.')||t.includes('previous us')) return {page:'P7',node};
    if(t.includes('point of contact')||t.includes('u.s. contact')) return {page:'P8',node};
    if(t.includes('family')&&!t.includes('spouse')) return {page:'P9A',node};
    if(t.includes('spouse')||t.includes('marital')) return {page:'P9B',node};
    if(t.includes('present work')||t.includes('present employ')) return {page:'P10',node};
    if(t.includes('previous employ')) return {page:'P11',node};
    if(t.includes('additional work')||t.includes('background information 1')) return {page:'P12',node};
    if(t.includes('security')&&t.includes('1')) return {page:'P13',node};
    if(t.includes('security')&&t.includes('2')) return {page:'P14',node};
    if(t.includes('security')&&t.includes('3')) return {page:'P15',node};
    if(t.includes('security')&&t.includes('4')) return {page:'P16',node};
    if(t.includes('security')&&t.includes('5')) return {page:'P17',node};
    if(t.includes('prepared')) return {page:'PFINAL',node};
    return {page:'UNKNOWN',node};
  }

  const PNAMES={P1:'Personal 1',P2:'Personal 2',P3:'Dirección',P4:'Pasaporte',
    P5:'Viaje',P6:'Compañeros',P7:'Viajes Previos',P8:'Contacto EE.UU.',
    P9A:'Familia',P9B:'Cónyuge',P10:'Trabajo',P11:'Edu/Emp.Ant.',
    P12:'Info Adicional',P13:'Seguridad 1',P14:'Seguridad 2',
    P15:'Seguridad 3',P16:'Seguridad 4',P17:'Seguridad 5',PFINAL:'Preparador'};

  function $id(id){return document.getElementById(id);}
  function setStatus(msg,bg,color){
    const s=$id('tvrd-sta');if(!s)return;
    s.textContent=msg;s.style.background=bg||'#EAF0FF';s.style.color=color||'#001F73';
  }
  function setProgress(pct,msg){
    const pw=$id('tvrd-pw');if(pw)pw.style.display='block';
    const pr=$id('tvrd-pr');if(pr)pr.style.width=pct+'%';
    if(msg)setStatus(msg);
  }
  function clickNext(){
    // Suprimir popup "abandonar" antes de navegar
    window.onbeforeunload=null;
    try{window.removeEventListener('beforeunload',window._ceacBU);}catch(e){}
    // Click Next3
    const next3=$id('ctl00_SiteContentPlaceHolder_UpdateButton3');
    if(next3&&next3.offsetParent!==null){next3.click();return true;}
    return false;
  }

  // Manejar Save Confirmation — si aparece, click Continue Application
  function handleSavePage(){
    const h1=document.querySelector('h1,h2');
    if(h1&&h1.textContent.includes('Save Confirmation')){
      const cont=document.querySelector('input[value*="Continue"],a[href*="Continue"]');
      if(cont){cont.click();return true;}
    }
    return false;
  }

  function refreshUI(){
    const{page,node}=detectPage();
    const pgEl=$id('tvrd-pg');if(pgEl)pgEl.textContent=PNAMES[page]||node||'?';
    chrome.storage.local.get('ds160',r=>{
      const data=r.ds160;
      if(data&&data.fields){
        const m=data.meta||{};
        const cli=$id('tvrd-cli');
        const nombre=(data.fields.q2_nombre||m.nombre||'').trim();
        const apellido=(data.fields.q1_apellido||m.apellido||'').trim();
        if(cli)cli.textContent=(nombre+' '+apellido).trim()+(m.completeness_pct?' · '+m.completeness_pct+'%':'');
        const btn=$id('tvrd-btn');
        if(page==='UNKNOWN'){
          setStatus('⚠️ No mapeada — '+node,'#FFF4DE','#92400E');
          if(btn){btn.disabled=true;btn.style.opacity='.4';}
        }else{
          setStatus('✅ Listo — '+(PNAMES[page]||page),'#EAF8EE','#15803d');
          if(btn){btn.disabled=false;btn.style.opacity='1';}
        }
      }else{
        setStatus('Carga el JSON desde el popup','#FFF4DE','#92400E');
        const btn=$id('tvrd-btn');if(btn){btn.disabled=true;btn.style.opacity='.4';}
      }
    });
  }
  refreshUI();

  let collapsed=false;
  $id('tvrd-hdr').addEventListener('click',()=>{
    const b=$id('tvrd-body'),t=$id('tvrd-tog');
    collapsed=!collapsed;b.style.display=collapsed?'none':'block';t.textContent=collapsed?'▼':'▲';
  });

  $id('tvrd-btn').addEventListener('click',()=>{
    chrome.storage.local.get('ds160',async r=>{
      if(!r.ds160)return;
      const btn=$id('tvrd-btn');
      if(btn){btn.disabled=true;btn.textContent='⏳ Llenando...';}
      try{await fillPage(r.ds160,detectPage().page);}
      catch(e){setStatus('❌ '+e.message,'#FFF5F5','#DC2626');console.error('[TVRD]',e);}
      if(btn){btn.disabled=false;btn.textContent='▶ Llenar página';}
    });
  });

  $id('tvrd-next').addEventListener('click',()=>clickNext());

  let autoRunning=false;
  $id('tvrd-auto').addEventListener('click',function(){
    if(autoRunning){
      autoRunning=false;
      this.textContent='⚡ AUTO CEAC v2';
      this.style.background='#7C3AED';
      setStatus('⏹ Auto detenido','#FFF4DE','#92400E');
      return;
    }
    chrome.storage.local.get('ds160',async r=>{
      if(!r.ds160){setStatus('Carga el JSON primero','#FFF4DE','#92400E');return;}
      autoRunning=true;
      const autoBtn=$id('tvrd-auto');
      if(autoBtn){autoBtn.textContent='⏹ DETENER AUTO';autoBtn.style.background='#DC2626';}

      async function step(){
        if(!autoRunning)return;
        const{page}=detectPage();
        if(page==='PFINAL'||page==='UNKNOWN'){
          autoRunning=false;
          if(autoBtn){autoBtn.textContent='⚡ AUTO CEAC v2';autoBtn.style.background='#7C3AED';}
          setStatus(page==='PFINAL'?'🏁 Completo — revisa y firma':'⚠️ Página no mapeada','#EAF8EE','#15803d');
          return;
        }
        setStatus('🤖 Llenando '+(PNAMES[page]||page)+'...','#EAF0FF','#001F73');
        const btn=$id('tvrd-btn');if(btn){btn.disabled=true;btn.textContent='⏳...';}
        try{
          await fillPage(r.ds160,page);
          for(let i=4;i>0;i--){
            if(!autoRunning)return;
            const nb=$id('tvrd-next');if(nb)nb.textContent='Next ('+i+'s)';
            setStatus('✅ '+(PNAMES[page]||page)+' — Next en '+i+'s','#EAF8EE','#15803d');
            await new Promise(res=>setTimeout(res,1000));
          }
          const nb=$id('tvrd-next');if(nb)nb.textContent='Next ›';
          if(!autoRunning)return;
          clickNext();
          await new Promise(res=>setTimeout(res,1500));
          // Si apareció Save Confirmation, hacer click en Continue
          handleSavePage();
          const prevPage=page;let waited=0;
          await new Promise(res=>{
            const iv=setInterval(()=>{
              waited+=400;
              const{page:np}=detectPage();
              if(np!==prevPage||waited>=15000){clearInterval(iv);res();}
            },400);
          });
          await new Promise(res=>setTimeout(res,1200));
          refreshUI();
          step();
        }catch(err){
          autoRunning=false;
          if(autoBtn){autoBtn.textContent='⚡ AUTO CEAC v2';autoBtn.style.background='#7C3AED';}
          setStatus('❌ Error: '+err.message,'#FFF5F5','#DC2626');
        }
      }
      step();
    });
  });

  async function fillPage(data,page){
    const F=data.fields||{};
    const P='ctl00_SiteContentPlaceHolder_FormView1_';
    function g(k,def=''){const v=F[k];return(v!=null&&String(v).trim()&&!['null','None','undefined',''].includes(String(v).trim()))?String(v).trim():def;}
    function yn(k){return['YES','SI','SÍ','TRUE','1'].includes(g(k,'NO').toUpperCase());}
    function gd(k){
      const v=g(k);if(!v)return{d:'',m:'',y:''};
      try{const dt=new Date(v+'T12:00:00');const M=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];return{d:String(dt.getDate()),m:M[dt.getMonth()],y:String(dt.getFullYear())};}
      catch{return{d:'',m:'',y:''};}
    }
    function fi(id,v){if(!v&&v!==0)return false;const e=document.getElementById(id);if(!e)return false;e.value=String(v);['input','change','blur'].forEach(ev=>e.dispatchEvent(new Event(ev,{bubbles:true})));return true;}
    function se(id,val,byText=false){
      if(!val)return false;const e=document.getElementById(id);if(!e||e.tagName!=='SELECT')return false;
      const opts=Array.from(e.options);const v=String(val).toUpperCase();
      const m=byText?opts.find(o=>o.text.toUpperCase().includes(v)):opts.find(o=>o.value.toUpperCase()===v||o.value.toUpperCase().includes(v)||o.text.toUpperCase().includes(v));
      if(m){e.value=m.value;e.dispatchEvent(new Event('change',{bubbles:true}));return true;}return false;
    }
    function cb(id,chk){const e=document.getElementById(id);if(!e)return false;if(chk&&!e.checked)e.click();else if(!chk&&e.checked)e.click();return true;}
    function cl(id){const e=document.getElementById(id);if(e){e.click();return true;}return false;}
    function ta(id,v){if(!v)return;const e=document.getElementById(id);if(e){e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));}}
    function W(ms){return new Promise(r=>setTimeout(r,ms));}

    if(page==='P1'){
      setProgress(10,'Nombre y apellido...');
      fi(P+'tbxAPP_SURNAME',g('q1_apellido'));fi(P+'tbxAPP_GIVEN_NAME',g('q2_nombre'));
      const nat=g('q6_nombre_nativo');cb(P+'cbexAPP_FULL_NAME_NATIVE_NA',!nat);if(nat)fi(P+'tbxAPP_FULL_NAME_NATIVE',nat);
      cl(P+'rblOtherNames_1');cl(P+'rblTelecodeQuestion_1');
      setProgress(45,'Sexo, civil, nacimiento...');
      se(P+'ddlAPP_GENDER',g('q7_sexo','M').toUpperCase()==='F'?'F':'M');
      // Marital Status — valores exactos del CEAC
      const civRaw=g('q8_civil','soltero').toLowerCase();
      const civMap={
        'soltero':'SINGLE','single':'SINGLE',
        'casado':'MARRIED','married':'MARRIED',
        'union_libre':'COMMON LAW MARRIAGE','union libre':'COMMON LAW MARRIAGE',
        'common_law':'COMMON LAW MARRIAGE','common law':'COMMON LAW MARRIAGE',
        'divorciado':'DIVORCED','divorced':'DIVORCED',
        'viudo':'WIDOWED','widowed':'WIDOWED',
        'separado':'LEGALLY SEPARATED','separated':'LEGALLY SEPARATED',
        'civil':'CIVIL UNION/DOMESTIC PARTNERSHIP',
      };
      let civVal='SINGLE';
      for(const[k,v]of Object.entries(civMap)){if(civRaw.includes(k)){civVal=v;break;}}
      se(P+'ddlAPP_MARITAL_STATUS',civVal,true);
      const db=gd('q9_dob');se(P+'ddlDOBDay',db.d);se(P+'ddlDOBMonth',db.m,true);fi(P+'tbxDOBYear',db.y);
      fi(P+'tbxAPP_POB_CITY',g('q10_ciudad_nac'));
      const prov=g('q11_prov_nac');cb(P+'cbexAPP_POB_ST_PROVINCE_NA',!prov);if(prov)fi(P+'tbxAPP_POB_ST_PROVINCE',prov);
      se(P+'ddlAPP_POB_CNTRY','DOMR');
    }
    else if(page==='P2'){
      setProgress(25,'Nacionalidad...');
      se(P+'ddlAPP_NATL','DOMR');cl(P+'rblAPP_OTH_NATL_IND_1');cl(P+'rblPermResOtherCntryInd_1');
      const ced=g('q20_cedula');cb(P+'cbexAPP_NATIONAL_ID_NA',!ced);
      if(ced){await W(200);fi(P+'tbxAPP_NATIONAL_ID',ced);}
      cb(P+'cbexAPP_SSN_NA',true);cb(P+'cbexAPP_TAX_ID_NA',true);
    }
    else if(page==='P3'){
      setProgress(15,'Dirección...');
      fi(P+'tbxAPP_ADDR_LN1',g('q23_dir1'));fi(P+'tbxAPP_ADDR_LN2',g('q24_dir2')||'');fi(P+'tbxAPP_ADDR_CITY',g('q25_ciudad'));
      const st=g('q26_provincia');cb(P+'cbexAPP_ADDR_STATE_NA',!st);if(st)fi(P+'tbxAPP_ADDR_STATE',st);
      const zip=g('q27_postal');cb(P+'cbexAPP_ADDR_POSTAL_CD_NA',!zip||zip.length<3);if(zip&&zip.length>=3)fi(P+'tbxAPP_ADDR_POSTAL_CD',zip);
      se(P+'ddlCountry','DOMR');cl(P+'rblMailingAddrSame_0');
      setProgress(55,'Teléfono y email...');
      fi(P+'tbxAPP_HOME_TEL',g('q33_tel'));
      const mob=g('q34_tel2');cb(P+'cbexAPP_MOBILE_TEL_NA',!mob);if(mob)fi(P+'tbxAPP_MOBILE_TEL',mob);
      cb(P+'cbexAPP_BUS_TEL_NA',true);cl(P+'rblAddPhone_1');
      fi(P+'tbxAPP_EMAIL_ADDR',g('q36_email'));cl(P+'rblAddEmail_1');
      // Redes sociales
      const hasSocial=g('q38_red1')||g('q37_redes','NO').toUpperCase()==='SI';
      if(hasSocial&&g('q38_red1')){
        // Primera red
        se(P+'dtlSocial_ctl00_ddlSocialMedia',g('q38_red1'),true);
        await W(300);
        fi(P+'dtlSocial_ctl00_tbxSocialMediaIdent',g('q39_user1')||g('q38_red1'));
        // Segunda red si existe
        if(g('q40_red2')&&g('q41_user2')){
          // Click Add Another si existe
          const addBtn=document.querySelector('a[id*="AddSocial"],input[id*="AddSocial"],a[href*="AddSocial"]');
          if(addBtn){addBtn.click();await W(500);
            se(P+'dtlSocial_ctl01_ddlSocialMedia',g('q40_red2'),true);
            await W(200);
            fi(P+'dtlSocial_ctl01_tbxSocialMediaIdent',g('q41_user2'));
          }
        }
        cl(P+'rblAddSocial_1'); // No más redes
      } else {
        cl(P+'rblAddSocial_1');
      }
    }
    else if(page==='P4'){
      setProgress(20,'Tipo de pasaporte — Regular...');
      const pptType=document.getElementById(P+'dlstPPT_TYPE')||document.querySelector('select[id*="PPT_TYPE"],select[id*="PassportType"]');
      if(pptType){const r=Array.from(pptType.options).find(o=>o.value==='R'||o.text.toUpperCase().includes('REGULAR')||o.text.toUpperCase().includes('ORDINARY'));if(r){pptType.value=r.value;pptType.dispatchEvent(new Event('change',{bubbles:true}));}}
      await W(300);
      fi(P+'tbxPPT_NUM',g('q43_numpas').replace(/\s+/g,''));
      cb(P+'cbexPPT_BOOK_NUM_NA',true);
      ['ddlPPT_ISSUED_CNTRY','ddlPPT_ISSUED_IN_CNTRY'].forEach(id=>se(P+id,'DOMR'));
      fi(P+'tbxPPT_ISSUED_IN_CITY',g('q46_ciudad_emision')||g('q25_ciudad'));
      cb(P+'cbexAPP_POB_ST_PROVINCE_NA',true);
      const pi=gd('q48_emision'),pe=gd('q49_vence');
      if(pi.d){se(P+'ddlPPT_ISSUED_DTEDay',pi.d);se(P+'ddlPPT_ISSUED_DTEMonth',pi.m,true);fi(P+'tbxPPT_ISSUEDYear',pi.y);}
      if(pe.d){se(P+'ddlPPT_EXPIRE_DTEDay',pe.d);se(P+'ddlPPT_EXPIRE_DTEMonth',pe.m,true);fi(P+'tbxPPT_EXPIREYear',pe.y);}
      cl(P+'rblLOST_PPT_IND_1');
    }
    else if(page==='P5'){
      setProgress(10,'Propósito del viaje...');
      const vSel=document.getElementById(P+'dlstPurposeOfTrip');
      if(vSel){const b=Array.from(vSel.options).find(o=>o.value==='B'||o.text.includes('PLEASURE'));if(b){vSel.value=b.value;vSel.dispatchEvent(new Event('change',{bubbles:true}));}}
      // Esperar que aparezca el select Specify (AJAX)
      await new Promise(res=>{
        let tries=0;
        const iv=setInterval(()=>{
          tries++;
          const sels=document.querySelectorAll('select');
          for(const s of sels){
            if(s.id===P+'dlstPurposeOfTrip') continue;
            const opts=Array.from(s.options);
            const b2=opts.find(o=>o.text.toUpperCase().includes('TOURISM')||o.text.toUpperCase().includes('PLEASURE')||o.text.toUpperCase().includes('B2'));
            if(b2&&opts.length>1){
              s.value=b2.value;
              s.dispatchEvent(new Event('change',{bubbles:true}));
              clearInterval(iv);res();return;
            }
          }
          if(tries>15){clearInterval(iv);res();}
        },300);
      });
      await W(400);
      setProgress(30,'Planes — No...');
      cl(P+'rblSpecificTravel_1');
      const rNo=document.querySelector('input[id*="SpecificTravel"][value="N"],input[id*="SpecificPlan"][value="N"]');if(rNo&&!rNo.checked)rNo.click();
      await W(400);
      setProgress(50,'Fecha estimada y 10 días...');
      // Buscar campos de fecha por múltiples IDs
      const arrFields=[
        {day:P+'ddlARRIVAL_US_DTEDay',mon:P+'ddlARRIVAL_US_DTEMonth',yr:P+'tbxARRIVAL_US_DTEYear'},
        {day:P+'ddlIntendedArrivalDay',mon:P+'ddlIntendedArrivalMonth',yr:P+'tbxIntendedArrivalYear'},
      ];
      for(const af of arrFields){
        const aD=$id(af.day);if(!aD) continue;
        aD.value='15';aD.dispatchEvent(new Event('change',{bubbles:true}));
        const aM=$id(af.mon);
        if(aM){const j=Array.from(aM.options).find(o=>o.text.toUpperCase().includes('SEP')||o.value==='SEP');if(j){aM.value=j.value;aM.dispatchEvent(new Event('change',{bubbles:true}));}}
        const aY=$id(af.yr);if(aY)fi(af.yr,'2026');
        break;
      }
      // Duración — 10 days
      const allInputs=document.querySelectorAll('input[type="text"]');
      for(const inp of allInputs){
        if((inp.id||'').toUpperCase().includes('STAY')&&(inp.id||'').toUpperCase().includes('LENGTH')){
          fi(inp.id,'10');break;
        }
      }
      const allSels=document.querySelectorAll('select');
      for(const s of allSels){
        if((s.id||'').toUpperCase().includes('STAY')){
          const d=Array.from(s.options).find(o=>o.text.toUpperCase().includes('DAY'));
          if(d){s.value=d.value;s.dispatchEvent(new Event('change',{bubbles:true}));break;}
        }
      }
      // Quién paga — Self
      for(const s of document.querySelectorAll('select')){
        if((s.id||'').toUpperCase().includes('PAY')||s.id===P+'ddlWHO_IS_PAYING'){
          const sOpt=Array.from(s.options).find(o=>o.value==='S'||o.text.toUpperCase().includes('SELF'));
          if(sOpt){s.value=sOpt.value;s.dispatchEvent(new Event('change',{bubbles:true}));break;}
        }
      }
      setProgress(70,'Quién paga — Self...');
      const pS=$id(P+'ddlWHO_IS_PAYING')||document.querySelector('select[id*="WHO_IS_PAYING"],select[id*="Payer"]');
      if(pS){const s=Array.from(pS.options).find(o=>o.value==='S'||o.text.toUpperCase().includes('SELF'));if(s){pS.value=s.value;pS.dispatchEvent(new Event('change',{bubbles:true}));}}
      await W(400);
      setProgress(90,'Compañeros — No...');
      cl(P+'rblOtherPersonsTraveling_1');
      const rA=document.querySelector('input[id*="OtherPersons"][value="N"],input[id*="TravelingWith"][value="N"]');if(rA&&!rA.checked)rA.click();
    }
    else if(page==='P6'){
      setProgress(50,'Sin compañeros...');
      cl(P+'rblOtherPersonsTraveling_1');
      document.querySelectorAll('input[type="radio"][value="N"]').forEach(e=>{if(!e.checked)e.click();});
    }
    else if(page==='P7'){
      setProgress(15,'¿Estuvo en EE.UU.?...');
      if(yn('q82_estuvo')){
        cl(P+'rblPREV_US_TRAVEL_IND_0');await W(400);
        const v1=gd('q83_fecha_vis1');
        if(v1.d){se(P+'dtlPREV_US_VISIT_ctl00_ddlPREV_US_VISIT_DTEDay',v1.d);se(P+'dtlPREV_US_VISIT_ctl00_ddlPREV_US_VISIT_DTEMonth',v1.m,true);fi(P+'dtlPREV_US_VISIT_ctl00_tbxPREV_US_VISIT_DTEYear',v1.y);}
        ta(P+'dtlPREV_US_VISIT_ctl00_tbxPREV_US_VISIT_LENGTH',g('q84_dur_vis1','6 months'));
      }else{cl(P+'rblPREV_US_TRAVEL_IND_1');}
      setProgress(40,'¿Visa anterior?...');
      if(yn('q87_visa_prev')){
        cl(P+'rblPREV_VISA_IND_0');await W(300);
        const ve=gd('q88_visa_emision');
        if(ve.d){se(P+'ddlPREV_VISA_ISSUED_DTEDay',ve.d);se(P+'ddlPREV_VISA_ISSUED_DTEMonth',ve.m,true);fi(P+'tbxPREV_VISA_ISSUED_DTEYear',ve.y);}
        fi(P+'tbxPREV_VISA_NUMBER',g('q89_visa_num','Do Not Know'));
        cl(P+'rblPREV_VISA_SAME_TYPE_IND_1');cl(P+'rblPREV_VISA_SAME_CNTRY_IND_1');cl(P+'rblPREV_VISA_10YR_MULTI_IND_1');
      }else{cl(P+'rblPREV_VISA_IND_1');}
      setProgress(65,'¿Negación?...');
      if(yn('q93_negacion')){
        cl(P+'rblPREV_VISA_REFUSED_IND_0');await W(300);
        ta(P+'tbxVISA_DENIAL_EXPL',g('q95_razon_neg')||g('q94_negacion_donde')||'Previously denied');
      }else{cl(P+'rblPREV_VISA_REFUSED_IND_1');}
      setProgress(85,'Petición — No...');cl(P+'rblIV_PETITION_IND_1');
    }
    else if(page==='P8'){
      setProgress(20,'Contacto EE.UU....');
      const noC=!g('q98_cont_ap')&&!g('q99_cont_nom');
      cb(P+'cbxUS_POC_NAME_NA',noC);
      if(!noC){fi(P+'tbxUS_POC_SURNAME',g('q98_cont_ap'));fi(P+'tbxUS_POC_GIVEN_NAME',g('q99_cont_nom'));}
      cb(P+'cbxUS_POC_ORG_NA_IND',true);
      setProgress(40,'Relación...');
      const relRaw=g('q101_cont_rel','OTHER').toUpperCase();
      const relMap={'AMIGO':'FRIEND','FRIEND':'FRIEND','AMIGA':'FRIEND','CONOCIDO':'FRIEND',
        'FAMILIAR':'RELATIVE','RELATIVE':'RELATIVE','PARIENTE':'RELATIVE','FAMILIA':'RELATIVE',
        'HERMANO':'RELATIVE','HERMANA':'RELATIVE','PRIMO':'RELATIVE','PRIMA':'RELATIVE',
        'TIO':'RELATIVE','TIA':'RELATIVE','EMPLEADOR':'EMPLOYER','EMPLOYER':'EMPLOYER',
        'HOTEL':'HOTEL','OTHER':'OTHER','OTRO':'OTHER','OTRA':'OTHER'};
      let relVal='OTHER';
      for(const[k,v]of Object.entries(relMap)){if(relRaw.includes(k)){relVal=v;break;}}
      se(P+'ddlUS_POC_REL_TO_APP',relVal);
      setProgress(60,'Dirección contacto...');
      fi(P+'tbxUS_POC_ADDR_LN1',g('q102_cont_dir'));fi(P+'tbxUS_POC_ADDR_CITY',g('q103_cont_ciudad'));
      se(P+'ddlUS_POC_ADDR_STATE',g('q104_cont_estado'),true);
      const zip=g('q105_cont_zip');cb(P+'cbexUS_POC_ADDR_POSTAL_CD_NA',!zip);if(zip)fi(P+'tbxUS_POC_ADDR_POSTAL_CD',zip);
      fi(P+'tbxUS_POC_HOME_TEL',g('q106_cont_tel'));
      const em=g('q107_cont_email');cb(P+'cbexUS_POC_EMAIL_ADDR_NA',!em);if(em)fi(P+'tbxUS_POC_EMAIL_ADDR',em);
    }
    else if(page==='P9A'){
      setProgress(15,'Padre...');
      const pa=g('q108_padre_ap'),pn=g('q109_padre_nom');
      cb(P+'cbxFATHER_SURNAME_UNK_IND',!pa);if(pa)fi(P+'tbxFATHER_SURNAME',pa);
      cb(P+'cbxFATHER_GIVEN_NAME_UNK_IND',!pn);if(pn)fi(P+'tbxFATHER_GIVEN_NAME',pn);
      const pd=gd('q110_padre_dob');cb(P+'cbxFATHER_DOB_UNK_IND',!pd.d);
      if(pd.d){se(P+'ddlFathersDOBDay',pd.d);se(P+'ddlFathersDOBMonth',pd.m,true);fi(P+'tbxFathersDOBYear',pd.y);}
      if(yn('q111_padre_eeuu'))cl(P+'rblFATHER_LIVE_IN_US_IND_0');else cl(P+'rblFATHER_LIVE_IN_US_IND_1');
      await W(200);
      setProgress(40,'Madre...');
      const ma=g('q113_madre_ap'),mn=g('q114_madre_nom');
      cb(P+'cbxMOTHER_SURNAME_UNK_IND',!ma);if(ma)fi(P+'tbxMOTHER_SURNAME',ma);
      cb(P+'cbxMOTHER_GIVEN_NAME_UNK_IND',!mn);if(mn)fi(P+'tbxMOTHER_GIVEN_NAME',mn);
      const md=gd('q115_madre_dob');cb(P+'cbxMOTHER_DOB_UNK_IND',!md.d);
      if(md.d){se(P+'ddlMothersDOBDay',md.d);se(P+'ddlMothersDOBMonth',md.m,true);fi(P+'tbxMothersDOBYear',md.y);}
      if(yn('q116_madre_eeuu'))cl(P+'rblMOTHER_LIVE_IN_US_IND_0');else cl(P+'rblMOTHER_LIVE_IN_US_IND_1');
      await W(200);
      setProgress(65,'Familiares inmediatos...');
      if(yn('q118_fam_inm')){
        cl(P+'rblUS_IMMED_RELATIVE_IND_0');await W(400);
        fi(P+'dtlUS_RELATIVE_ctl00_tbxUS_REL_SURNAME',g('q119_fam1_ap'));
        fi(P+'dtlUS_RELATIVE_ctl00_tbxUS_REL_GIVEN_NAME',g('q120_fam1_nom'));
        se(P+'dtlUS_RELATIVE_ctl00_ddlUS_REL_TYPE',g('q121_fam1_rel'),true);
        se(P+'dtlUS_RELATIVE_ctl00_ddlUS_REL_STATUS',g('q122_fam1_estatus'),true);
      }else{cl(P+'rblUS_IMMED_RELATIVE_IND_1');}
      setProgress(85,'Otros familiares — No...');
      // Intentar múltiples IDs para "Other Relatives"
      ['rblUS_OTHER_RELATIVE_IND_1','rblOTHER_RELATIVE_IND_1','rblUS_OTHR_REL_IND_1'].forEach(id=>cl(P+id));
      // Fallback — cualquier radio N que mencione OTHER y RELATIVE
      document.querySelectorAll('input[type="radio"]').forEach(e=>{
        const id=(e.id||'').toUpperCase();
        if((id.includes('OTHER')&&id.includes('RELAT'))&&e.value==='N'&&!e.checked)e.click();
      });
    }
    else if(page==='P9B'){
      setProgress(50,'Cónyuge...');
      fi(P+'tbxSpouseSurname',g('q125_con_ap'));fi(P+'tbxSpouseGivenName',g('q126_con_nom'));
      const sd=gd('q127_con_dob');if(sd.d){se(P+'ddlDOBDay',sd.d);se(P+'ddlDOBMonth',sd.m,true);fi(P+'tbxDOBYear',sd.y);}
      se(P+'ddlSpouseNatDropDownList','DOMR');fi(P+'tbxSpousePOBCity',g('q10_ciudad_nac'));se(P+'ddlSpousePOBCountry','DOMR');se(P+'ddlSpouseAddressType','H');
    }
    else if(page==='P10'){
      setProgress(10,'Ocupación...');
      const ocRaw=g('q131_ocupacion','EMPLOYED').toUpperCase();
      const ocMap={'EMPLOYED':'B','EMPLEADO':'B','EMPLOYEE':'B','EMPLEO':'B',
        'SELF-EMPLOYED':'F','SELF EMPLOYED':'F','INDEPENDIENTE':'F','EMPRESARIO':'F','BUSINESS OWNER':'F',
        'STUDENT':'S','ESTUDIANTE':'S','RETIRED':'R','JUBILADO':'R','PENSIONADO':'R',
        'UNEMPLOYED':'U','DESEMPLEADO':'U','HOMEMAKER':'H','AMA DE CASA':'H','OTHER':'O','OTRO':'O'};
      let ocVal='B';for(const[k,v]of Object.entries(ocMap)){if(ocRaw.includes(k)){ocVal=v;break;}}
      se(P+'ddlPresentOccupation',ocVal);
      // Esperar que el AJAX termine y aparezca el campo Employer
      await new Promise(res=>{
        let tries=0;
        const iv=setInterval(()=>{
          tries++;
          const emp=$id(P+'tbxEmpSchName');
          if(emp&&emp.offsetParent!==null){clearInterval(iv);res();return;}
          if(tries>20){clearInterval(iv);res();}
        },300);
      });
      await W(500);
      setProgress(35,'Empleador...');
      fi(P+'tbxEmpSchName',g('q132_empleador')||'Does Not Apply');
      fi(P+'tbxEmpSchAddr1',g('q133_dir_emp1')||'Does Not Apply');
      fi(P+'tbxEmpSchAddr2','');
      fi(P+'tbxEmpSchCity',g('q134_emp_ciudad')||g('q25_ciudad'));
      const stE=g('q135_emp_prov');cb(P+'cbxWORK_EDUC_ADDR_STATE_NA',!stE);if(stE)fi(P+'tbxWORK_EDUC_ADDR_STATE',stE);
      cb(P+'cbxWORK_EDUC_ADDR_POSTAL_CD_NA',true);
      fi(P+'tbxWORK_EDUC_TEL',g('q138_emp_tel')||g('q33_tel'));
      se(P+'ddlEmpSchCountry','DOMR');
      setProgress(60,'Fecha inicio...');
      const ei=gd('q139_emp_inicio');
      if(ei.d){se(P+'ddlEmpDateFromDay',ei.d);// Mes puede ser número o texto
      (function(){
        const mSel=$id(P+'ddlEmpDateFromMonth');
        if(!mSel||!ei.m) return;
        const opts=Array.from(mSel.options);
        const m=opts.find(o=>o.text.toUpperCase().startsWith(ei.m)||o.value===String(['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].indexOf(ei.m)+1));
        if(m){mSel.value=m.value;mSel.dispatchEvent(new Event('change',{bubbles:true}));}
      })();fi(P+'tbxEmpDateFromYear',ei.y);}
      setProgress(80,'Salario y funciones...');
      const sal=g('q140_salario');cb(P+'cbxCURR_MONTHLY_SALARY_NA',!sal);if(sal)fi(P+'tbxCURR_MONTHLY_SALARY',sal);
      await W(200);
      ta(P+'tbxDescribeDuties',g('q141_funciones')||'General administrative and management duties');
    }
    else if(page==='P11'){
      setProgress(25,'Empleo anterior...');
      if(yn('q142_emp_ant')){
        cl(P+'rblPreviouslyEmployed_0');await W(500);
        fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_NAME',g('q143_emp_ant_nom'));
        fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_ADDR',g('q144_dir_emp_ant'));
        fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_CITY',g('q25_ciudad'));
        fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_TEL',g('q145_tel_emp_ant'));
        fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_JOB_TITLE',g('q146_cargo_ant'));
        const es=gd('q147_inicio_ant'),ef=gd('q148_fin_ant');
        if(es.d){se(P+'dtlPrevEmploy_ctl00_ddlPREV_EMPLOY_FROM_DTEDay',es.d);se(P+'dtlPrevEmploy_ctl00_ddlPREV_EMPLOY_FROM_DTEMonth',es.m,true);fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_FROM_DTEYear',es.y);}
        if(ef.d){se(P+'dtlPrevEmploy_ctl00_ddlPREV_EMPLOY_TO_DTEDay',ef.d);se(P+'dtlPrevEmploy_ctl00_ddlPREV_EMPLOY_TO_DTEMonth',ef.m,true);fi(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_TO_DTEYear',ef.y);}
        ta(P+'dtlPrevEmploy_ctl00_tbxPREV_EMPLOY_DUTIES',g('q149_func_ant'));
      }else{cl(P+'rblPreviouslyEmployed_1');}
      setProgress(65,'Educación...');
      if(yn('q151_edu')){
        cl(P+'rblOtherEduc_0');await W(400);
        fi(P+'dtlPrevEduc_ctl00_tbxSchoolName',g('q152_escuela'));
        fi(P+'dtlPrevEduc_ctl00_tbxSchoolAddr1',g('q153_escuela_dir')||g('q23_dir1'));
        fi(P+'dtlPrevEduc_ctl00_tbxSchoolCity',g('q25_ciudad'));
        cb(P+'dtlPrevEduc_ctl00_cbxEDUC_INST_ADDR_STATE_NA',true);cb(P+'dtlPrevEduc_ctl00_cbxEDUC_INST_POSTAL_CD_NA',true);
        se(P+'dtlPrevEduc_ctl00_ddlSchoolCountry','DOMR');
        fi(P+'dtlPrevEduc_ctl00_tbxSchoolCourseOfStudy',g('q154_carrera')||'Business Administration');
        const ef=gd('q155_edu_inicio'),et=gd('q156_edu_fin');
        if(ef.d){se(P+'dtlPrevEduc_ctl00_ddlSchoolFromDay',ef.d);se(P+'dtlPrevEduc_ctl00_ddlSchoolFromMonth',ef.m,true);fi(P+'dtlPrevEduc_ctl00_tbxSchoolFromYear',ef.y);}
        if(et.d){se(P+'dtlPrevEduc_ctl00_ddlSchoolToDay',et.d);se(P+'dtlPrevEduc_ctl00_ddlSchoolToMonth',et.m,true);fi(P+'dtlPrevEduc_ctl00_tbxSchoolToYear',et.y);}
      }else{cl(P+'rblOtherEduc_1');}
    }
    else if(page==='P12'){
      setProgress(15,'Info adicional...');
      cl(P+'rblCLAN_TRIBE_IND_1');
      fi(P+'dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME',g('q160_idiomas','Spanish'));
      cl(P+'rblCOUNTRIES_VISITED_IND_1');cl(P+'rblORGANIZATION_IND_1');
      cl(P+'rblSPECIALIZED_SKILLS_IND_1');cl(P+'rblMILITARY_SERVICE_IND_1');cl(P+'rblINSURGENT_ORG_IND_1');
    }
    else if(page==='P13'){
      setProgress(30,'Salud — No...');
      cl(P+'rblDisease_1');await W(100);cl(P+'rblDisorder_1');await W(100);cl(P+'rblDruguser_1');
    }
    else if(page==='P14'){
      setProgress(10,'Criminal — No...');
      const s14=['Arrested','ControlledSubstances','Prostitution','MoneyLaundering','HumanTrafficking','AssistedSevereTrafficking','HumanTraffickingRelated'];
      for(let i=0;i<s14.length;i++){cl(P+'rbl'+s14[i]+'_1');await W(80);setProgress(10+Math.round(i/s14.length*85));}
    }
    else if(['P15','P16','P17'].includes(page)){
      setProgress(15,'Seguridad — todo No...');
      const radios=document.querySelectorAll('input[type="radio"]');
      let cnt=0;
      for(const r of radios){if(r.value==='N'&&!r.checked){r.click();await W(60);cnt++;}}
      setProgress(100,'✅ '+page+' listo — '+cnt+' radios');
    }
    else if(page==='PFINAL'){
      setProgress(50,'Idiomas y preparador...');
      fi(P+'tbxLangs',g('q160_idiomas','Spanish'));
      fi(P+'dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME',g('q160_idiomas','Spanish'));
      cl(P+'rblPREPARED_IND_1');
      document.querySelectorAll('input[type="radio"]').forEach(e=>{if((e.id||'').toLowerCase().includes('prepared')&&e.value==='N'&&!e.checked)e.click();});
      setProgress(100,'🏁 PFINAL — revisar y firmar');
    }else{
      setStatus('⚠️ Página no mapeada — llena manual','#FFF4DE','#92400E');return;
    }
    const btn=$id('tvrd-btn');if(btn){btn.disabled=false;btn.textContent='▶ Llenar página';}
    if(page!=='PFINAL')setStatus('✅ '+(PNAMES[page]||page)+' llenado','#EAF8EE','#15803d');
  }
})();
