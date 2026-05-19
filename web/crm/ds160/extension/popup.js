let DATA=null;
function show(s){['init','loaded','filling','done'].forEach(x=>{const el=document.getElementById('s-'+x);if(el)el.style.display=x===s?'block':'none';});}
function procesarJSON(text){try{DATA=JSON.parse(text);const m=DATA.meta||{},f=DATA.fields||{};chrome.storage.local.set({ds160:DATA});document.getElementById('cn').textContent=((m.nombre||'')+' '+(m.apellido||'')).trim();document.getElementById('ci').textContent='Pas: '+(m.pasaporte||'—')+' · '+(m.completeness_pct||'?')+'% · '+(m.filled_fields||0)+'/'+(m.total_fields||212)+' campos';const filled=Object.entries(f).filter(([k,v])=>v&&v!=='null');document.getElementById('prev').innerHTML=filled.slice(0,12).map(([k,v])=>'<div class="fr"><span class="fk">'+k+'</span><span class="fv">'+v+'</span></div>').join('')+(filled.length>12?'<div class="fr" style="color:#94A3B8">...y '+(filled.length-12)+' más</div>':'');show('loaded');}catch(err){alert('Error JSON: '+err.message);}}
document.getElementById('btn-cargar').addEventListener('click',async function(){try{if(window.showOpenFilePicker){const[fh]=await window.showOpenFilePicker({types:[{description:'JSON DS-160',accept:{'application/json':['.json']}}]});procesarJSON(await(await fh.getFile()).text());}else{const inp=document.createElement('input');inp.type='file';inp.accept='.json';inp.addEventListener('change',function(){if(!this.files[0])return;const r=new FileReader();r.onload=e=>procesarJSON(e.target.result);r.readAsText(this.files[0]);});inp.click();}}catch(e){if(e.name!=='AbortError')alert('Error: '+e.message);}});
document.getElementById('btn-ceac').addEventListener('click',function(){chrome.tabs.create({url:'https://ceac.state.gov/GenNIV/Default.aspx'});});
async function doFill(){if(!DATA)return;const tabs=await chrome.tabs.query({active:true,currentWindow:true});const tab=tabs[0];if(!tab||!tab.url||!tab.url.includes('ceac.state.gov')){alert('⚠️ Abre ceac.state.gov primero.\nNavega al formulario DS-160 y presiona Llenar.');return;}show('filling');try{await chrome.scripting.executeScript({target:{tabId:tab.id},func:fillCurrentPage,args:[DATA]});chrome.runtime.onMessage.addListener(function handler(msg){if(msg.type==='progress'){document.getElementById('pf').style.width=msg.pct+'%';document.getElementById('pl').textContent=msg.pct+'%';document.getElementById('fst').textContent=msg.step;}if(msg.type==='done'){chrome.runtime.onMessage.removeListener(handler);show('done');}if(msg.type==='error'){chrome.runtime.onMessage.removeListener(handler);alert('Error: '+msg.msg+'\nLlena ese campo manualmente.');show('done');}});}catch(e){alert('Error: '+e.message);show('loaded');}}
document.getElementById('btn-fill').addEventListener('click',doFill);
document.getElementById('btn-sig').addEventListener('click',doFill);
document.getElementById('btn-rep').addEventListener('click',function(){if(!DATA)return;const m=DATA.meta||{},f=DATA.fields||{};const filled=Object.entries(f).filter(([k,v])=>v&&v!=='null');const miss=Object.entries(f).filter(([k,v])=>!v||v==='null');let t='DS-160 TengoVisaRD\nCliente: '+m.nombre+' '+m.apellido+'\nPasaporte: '+m.pasaporte+'\nCompletitud: '+m.completeness_pct+'%\n\nCAMPOS:\n';filled.forEach(([k,v])=>t+=k.padEnd(28)+' '+v+'\n');t+='\nVACÍOS:\n';miss.slice(0,40).forEach(([k])=>t+=k+'\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:'text/plain'}));a.download='ds160_'+(m.email||'cliente')+'.txt';a.click();});
['btn-reset','btn-new'].forEach(id=>{const el=document.getElementById(id);if(el)el.addEventListener('click',function(){DATA=null;chrome.storage.local.remove('ds160');show('init');});});
chrome.storage.local.get('ds160',function(r){if(r.ds160){DATA=r.ds160;const m=DATA.meta||{};document.getElementById('cn').textContent=((m.nombre||'')+' '+(m.apellido||'')).trim();document.getElementById('ci').textContent='Pas: '+(m.pasaporte||'—')+' · '+(m.completeness_pct||'?')+'%';show('loaded');}});

function fillCurrentPage(data){
  const F=data.fields||{};
  const PRE='ctl00_SiteContentPlaceHolder_FormView1_';
  function g(k,d=''){const v=F[k];return(v&&String(v).trim()&&v!=='null'&&v!=='None')?String(v).trim():d;}
  function gd(k){const v=g(k);if(!v)return{day:'',month:'',year:''};try{const d=new Date(v+'T12:00:00');const M=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];return{day:String(d.getDate()),month:M[d.getMonth()],year:String(d.getFullYear())};}catch{return{day:'',month:'',year:''};}};
  function yn(k){return['YES','SI','SÍ','TRUE'].includes(g(k,'NO').toUpperCase());}
  function fi(id,v){if(!v||v==='null')return false;const e=document.getElementById(id);if(!e)return false;e.value=v;['change','input','blur'].forEach(ev=>e.dispatchEvent(new Event(ev,{bubbles:true})));return true;}
  function se(id,v,byText=false){if(!v)return false;const e=document.getElementById(id);if(!e||e.tagName!=='SELECT')return false;const opts=Array.from(e.options);const m=byText?opts.find(o=>o.text.toUpperCase().includes(v.toUpperCase())):opts.find(o=>o.value.toUpperCase()===v.toUpperCase()||o.value.toUpperCase().includes(v.toUpperCase()));if(m){e.value=m.value;e.dispatchEvent(new Event('change',{bubbles:true}));return true;}return false;}
  function cb(id,check){const e=document.getElementById(id);if(!e)return false;if(check&&!e.checked)e.click();else if(!check&&e.checked)e.click();return true;}
  function ra(name,yes=true){const idx=yes?0:1;const e=document.getElementById(PRE+'rbl'+name+'_'+idx)||document.querySelector('input[id*="'+name+'"][value="'+(yes?'Y':'N')+'"]');if(e){e.click();return true;}return false;}
  function ta(id,v){if(!v)return;const e=document.getElementById(id);if(e){e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));}}
  function clickNext(){const ids=['ctl00_ucNavigateOption_ucNavPanel_ctl01_btnNextPageComplete','ctl00_SiteContentPlaceHolder_UpdateButton2','ctl00_SiteContentPlaceHolder_UpdateButton1'];for(const id of ids){const e=document.getElementById(id);if(e){e.click();return true;}}return false;}
  function send(pct,step){chrome.runtime.sendMessage({type:'progress',pct,step});}
  function delay(ms){return new Promise(r=>setTimeout(r,ms));}

  function detectPage(){
    const d=document;
    const has=id=>!!d.getElementById(PRE+id);
    if(has('tbxAPP_SURNAME'))return'P1';
    if(has('ddlAPP_NATL'))return'P2';
    if(has('tbxAPP_ADDR_LN1'))return'P3';
    if(has('tbxAPP_PASSPORT_NUM')||has('tbxPPT_NUM')||d.querySelector('input[id*="PASSPORT_NUM"]'))return'P4';
    if(has('tbxPayerPhone')||has('ddlPayerRelationship'))return'P5B';
    if(d.querySelector('input[id*="TRAVEL_PURPOSE"]')||d.querySelector('select[id*="TRAVEL_PURPOSE"]'))return'P5A';
    if(has('tbxUS_POC_SURNAME'))return'P8';
    if(has('tbxSpouseSurname'))return'P9B';
    if(has('tbxFATHER_SURNAME'))return'P9A';
    if(has('ddlPresentOccupation'))return'P10';
    if(has('rblPreviouslyEmployed_0'))return'P11';
    if(has('rblCLAN_TRIBE_IND_0'))return'P12';
    if(has('rblDisease_0'))return'P13';
    if(has('rblArrested_0'))return'P14';
    if(d.querySelector('input[id*="rblTerror"]')||d.querySelector('input[id*="Terror"]'))return'P15';
    if(d.querySelector('input[id*="Overstay"]')||d.querySelector('input[id*="OVERSTAY"]'))return'P16';
    if(has('tbxLangs')||d.querySelector('input[id*="Langs"]'))return'PFINAL';
    return'UNKNOWN';
  }

  async function run(){
    try{
      const page=detectPage();
      send(5,'Página: '+page);
      await delay(300);

      // ══ P1 — INFORMACIÓN PERSONAL ══
      if(page==='P1'){
        send(15,'Apellido y nombre...');
        fi(PRE+'tbxAPP_SURNAME',g('q1_apellido'));
        fi(PRE+'tbxAPP_GIVEN_NAME',g('q2_nombre'));
        const noNat=!g('q6_nombre_nativo');
        cb(PRE+'cbexAPP_FULL_NAME_NATIVE_NA',noNat);
        if(!noNat)fi(PRE+'tbxAPP_FULL_NAME_NATIVE',g('q6_nombre_nativo'));
        // Otros nombres — N
        const rOn1=document.getElementById(PRE+'rblOtherNames_1');if(rOn1)rOn1.click();
        // Telecode — N
        const rTc1=document.getElementById(PRE+'rblTelecodeQuestion_1');if(rTc1)rTc1.click();
        send(40,'Sexo y estado civil...');
        se(PRE+'ddlAPP_GENDER',g('q7_sexo','M').toUpperCase()==='M'?'M':'F');
        const cm={soltero:'S',single:'S',casado:'M',married:'M',viudo:'W',widowed:'W',divorciado:'D',divorced:'D',separado:'SP'};
        se(PRE+'ddlAPP_MARITAL_STATUS',cm[g('q8_civil','').toLowerCase()]||'S');
        send(65,'Fecha y lugar nacimiento...');
        const db=gd('q9_dob');
        se(PRE+'ddlDOBDay',db.day);
        se(PRE+'ddlDOBMonth',db.month,true);
        fi(PRE+'tbxDOBYear',db.year);
        fi(PRE+'tbxAPP_POB_CITY',g('q10_ciudad_nac'));
        const prov=g('q11_prov_nac');
        cb(PRE+'cbexAPP_POB_ST_PROVINCE_NA',!prov);
        if(prov)fi(PRE+'tbxAPP_POB_ST_PROVINCE',prov);
        se(PRE+'ddlAPP_POB_CNTRY','DOMR');
      }

      // ══ P2 — NACIONALIDAD ══
      else if(page==='P2'){
        send(20,'Nacionalidad...');
        se(PRE+'ddlAPP_NATL','DOMR');
        // Otra nacionalidad — N
        const rON1=document.getElementById(PRE+'rblAPP_OTH_NATL_IND_1');if(rON1)rON1.click();
        // Residente permanente otro país — N
        const rPR1=document.getElementById(PRE+'rblPermResOtherCntryInd_1');if(rPR1)rPR1.click();
        send(55,'Cédula...');
        const ced=g('q20_cedula');
        cb(PRE+'cbexAPP_NATIONAL_ID_NA',!ced);
        if(ced){await delay(150);fi(PRE+'tbxAPP_NATIONAL_ID',ced);}
        send(80,'SSN y Tax ID — N/A...');
        cb(PRE+'cbexAPP_SSN_NA',true);
        cb(PRE+'cbexAPP_TAX_ID_NA',true);
      }

      // ══ P3 — DIRECCIÓN Y CONTACTO ══
      else if(page==='P3'){
        send(15,'Dirección...');
        fi(PRE+'tbxAPP_ADDR_LN1',g('q23_dir1'));
        fi(PRE+'tbxAPP_ADDR_LN2',g('q24_dir2'));
        fi(PRE+'tbxAPP_ADDR_CITY',g('q25_ciudad'));
        const st=g('q26_provincia');
        cb(PRE+'cbexAPP_ADDR_STATE_NA',!st);
        if(st)fi(PRE+'tbxAPP_ADDR_STATE',st);
        const zip=g('q27_postal');
        cb(PRE+'cbexAPP_ADDR_POSTAL_CD_NA',!zip);
        if(zip)fi(PRE+'tbxAPP_ADDR_POSTAL_CD',zip);
        se(PRE+'ddlCountry','DOMR');
        // Mailing same — Y
        const rMS0=document.getElementById(PRE+'rblMailingAddrSame_0');if(rMS0)rMS0.click();
        send(50,'Teléfonos...');
        fi(PRE+'tbxAPP_HOME_TEL',g('q33_tel'));
        const mob=g('q34_tel2');
        cb(PRE+'cbexAPP_MOBILE_TEL_NA',!mob);
        if(mob)fi(PRE+'tbxAPP_MOBILE_TEL',mob);
        const bus=g('q35_tel_trab');
        cb(PRE+'cbexAPP_BUS_TEL_NA',!bus);
        if(bus)fi(PRE+'tbxAPP_BUS_TEL',bus);
        // Add phone — N
        const rAP1=document.getElementById(PRE+'rblAddPhone_1');if(rAP1)rAP1.click();
        send(75,'Email y redes...');
        fi(PRE+'tbxAPP_EMAIL_ADDR',g('q36_email'));
        // Add email — N
        const rAE1=document.getElementById(PRE+'rblAddEmail_1');if(rAE1)rAE1.click();
        // Redes sociales
        if(g('q38_red1')&&g('q39_user1')){
          se(PRE+'dtlSocial_ctl00_ddlSocialMedia',g('q38_red1'),true);
          fi(PRE+'dtlSocial_ctl00_tbxSocialMediaIdent',g('q39_user1'));
        }
        // Add social — N
        const rAS1=document.getElementById(PRE+'rblAddSocial_1');if(rAS1)rAS1.click();
      }

      // ══ P4 — PASAPORTE (IDs aproximados — verificar) ══
      else if(page==='P4'){
        send(20,'Pasaporte...');
        // Intentar múltiples variantes de IDs
        ['tbxAPP_PASSPORT_NUM','tbxPPT_NUM'].forEach(id=>fi(PRE+id,g('q43_numpas')));
        se(PRE+'ddlAPP_POB_CNTRY','DOMR');// País emisor — fallback
        ['ddlAPP_PASSPORT_ISSUED_COUNTRY','ddlPPT_ISSUED_CNTRY','ddlAPP_ISSUED_CNTRY'].forEach(id=>se(PRE+id,'DOMR'));
        send(60,'Fechas pasaporte...');
        const pi=gd('q48_emision'),pe=gd('q49_vence');
        ['ddlAPP_PASSPORT_ISSUED_DAY','ddlPPT_ISSUED_DAY'].forEach(id=>se(PRE+id,pi.day));
        ['ddlAPP_PASSPORT_ISSUED_MONTH','ddlPPT_ISSUED_MONTH','dlstPPT_ISSUE_MONTH'].forEach(id=>se(PRE+id,pi.month,true));
        ['tbxAPP_PASSPORT_ISSUED_YEAR','tbxPPT_ISSUE_YR'].forEach(id=>fi(PRE+id,pi.year));
        ['ddlAPP_PASSPORT_EXPIRE_DAY','ddlPPT_EXPIRE_DAY'].forEach(id=>se(PRE+id,pe.day));
        ['ddlAPP_PASSPORT_EXPIRE_MONTH','ddlPPT_EXPIRE_MONTH'].forEach(id=>se(PRE+id,pe.month,true));
        ['tbxAPP_PASSPORT_EXPIRE_YEAR','tbxPPT_EXPIRE_YR'].forEach(id=>fi(PRE+id,pe.year));
      }

      // ══ P5A — VIAJE (propósito, fechas, hospedaje) ══
      else if(page==='P5A'){
        send(20,'Propósito del viaje...');
        ['ddlTRAVEL_PURPOSE','ddlPURPOSE_OF_TRIP'].forEach(id=>se(PRE+id,'TOURISM',true));
        send(60,'Hospedaje y duración...');
        ['tbxUS_STREET_ADDR1','tbxUS_POC_ADDR_LN1'].forEach(id=>fi(PRE+id,g('q65_dir_hospedaje')));
        ['tbxUS_CITY','tbxUS_POC_ADDR_CITY'].forEach(id=>fi(PRE+id,g('q66_ciudad_hosp')));
        ['ddlUS_STATE','ddlUS_POC_ADDR_STATE'].forEach(id=>se(PRE+id,g('q67_estado_hosp'),true));
        ['tbxUS_ZIP','tbxUS_POC_ADDR_POSTAL_CD'].forEach(id=>fi(PRE+id,g('q105_cont_zip')||'00000'));
      }

      // ══ P5B — VIAJE (pago y compañeros) ══
      else if(page==='P5B'){
        send(30,'Datos del pago...');
        fi(PRE+'tbxPayerPhone',g('q33_tel'));
        const pe=g('q36_email');
        cb(PRE+'cbxDNAPAYER_EMAIL_ADDR_NA',!pe);
        if(pe)fi(PRE+'tbxPAYER_EMAIL_ADDR',pe);
        // Relación pagador — self
        se(PRE+'ddlPayerRelationship','S');
        // Dirección pagador — misma que solicitante
        const rPA0=document.getElementById(PRE+'rblPayerAddrSameAsInd_0');if(rPA0)rPA0.click();
        send(60,'Compañeros de viaje...');
        // No hay otros viajeros — N
        const rOP1=document.getElementById(PRE+'rblOtherPersonsTravelingWithYou_1');if(rOP1)rOP1.click();
      }

      // ══ P8 — CONTACTO EN EE.UU. ══
      else if(page==='P8'){
        send(20,'Contacto EE.UU....');
        fi(PRE+'tbxUS_POC_SURNAME',g('q98_cont_ap'));
        fi(PRE+'tbxUS_POC_GIVEN_NAME',g('q99_cont_nom'));
        cb(PRE+'cbxUS_POC_NAME_NA',!g('q98_cont_ap'));
        const org=g('q100_cont_org');
        cb(PRE+'cbxUS_POC_ORG_NA_IND',!org);
        if(org)fi(PRE+'tbxUS_POC_ORGANIZATION',org);
        const rm={AMIGO:'F',FRIEND:'F',FAMILIAR:'R',RELATIVE:'R',EMPLEADOR:'E',EMPLOYER:'E',HOTEL:'H',OTHER:'O',OTRO:'O'};
        se(PRE+'ddlUS_POC_REL_TO_APP',rm[g('q101_cont_rel','OTHER').toUpperCase()]||'O');
        send(55,'Dirección contacto...');
        fi(PRE+'tbxUS_POC_ADDR_LN1',g('q102_cont_dir'));
        fi(PRE+'tbxUS_POC_ADDR_LN2','');
        fi(PRE+'tbxUS_POC_ADDR_CITY',g('q103_cont_ciudad'));
        se(PRE+'ddlUS_POC_ADDR_STATE',g('q104_cont_estado'),true);
        fi(PRE+'tbxUS_POC_ADDR_POSTAL_CD',g('q105_cont_zip')||'00000');
        fi(PRE+'tbxUS_POC_HOME_TEL',g('q106_cont_tel'));
        const em=g('q107_cont_email');
        cb(PRE+'cbexUS_POC_EMAIL_ADDR_NA',!em);
        if(em)fi(PRE+'tbxUS_POC_EMAIL_ADDR',em);
      }

      // ══ P9A — FAMILIA (padre y madre) ══
      else if(page==='P9A'){
        send(20,'Padre...');
        const pa=g('q108_padre_ap'),pn=g('q109_padre_nom');
        cb(PRE+'cbxFATHER_SURNAME_UNK_IND',!pa);
        if(pa)fi(PRE+'tbxFATHER_SURNAME',pa);
        cb(PRE+'cbxFATHER_GIVEN_NAME_UNK_IND',!pn);
        if(pn)fi(PRE+'tbxFATHER_GIVEN_NAME',pn);
        const pd=gd('q110_padre_dob');
        if(pd.day){se(PRE+'ddlFathersDOBDay',pd.day);se(PRE+'ddlFathersDOBMonth',pd.month,true);fi(PRE+'tbxFathersDOBYear',pd.year);}
        else cb(PRE+'cbxFATHER_DOB_UNK_IND',true);
        const padreEEUU=yn('q111_padre_eeuu');
        const rFUS0=document.getElementById(PRE+'rblFATHER_LIVE_IN_US_IND_0');
        const rFUS1=document.getElementById(PRE+'rblFATHER_LIVE_IN_US_IND_1');
        if(padreEEUU&&rFUS0)rFUS0.click(); else if(rFUS1)rFUS1.click();
        send(55,'Madre...');
        const ma=g('q113_madre_ap'),mn=g('q114_madre_nom');
        cb(PRE+'cbxMOTHER_SURNAME_UNK_IND',!ma);
        if(ma)fi(PRE+'tbxMOTHER_SURNAME',ma);
        cb(PRE+'cbxMOTHER_GIVEN_NAME_UNK_IND',!mn);
        if(mn)fi(PRE+'tbxMOTHER_GIVEN_NAME',mn);
        const md=gd('q115_madre_dob');
        if(md.day){se(PRE+'ddlMothersDOBDay',md.day);se(PRE+'ddlMothersDOBMonth',md.month,true);fi(PRE+'tbxMothersDOBYear',md.year);}
        else cb(PRE+'cbxMOTHER_DOB_UNK_IND',true);
        const madreEEUU=yn('q116_madre_eeuu');
        const rMUS0=document.getElementById(PRE+'rblMOTHER_LIVE_IN_US_IND_0');
        const rMUS1=document.getElementById(PRE+'rblMOTHER_LIVE_IN_US_IND_1');
        if(madreEEUU&&rMUS0)rMUS0.click(); else if(rMUS1)rMUS1.click();
        send(80,'Familiares en EE.UU....');
        const rUI0=document.getElementById(PRE+'rblUS_IMMED_RELATIVE_IND_0');
        const rUI1=document.getElementById(PRE+'rblUS_IMMED_RELATIVE_IND_1');
        if(yn('q118_fam_inm')&&rUI0)rUI0.click(); else if(rUI1)rUI1.click();
        const rUO1=document.getElementById(PRE+'rblUS_OTHER_RELATIVE_IND_1');
        if(rUO1)rUO1.click();
      }

      // ══ P9B — CÓNYUGE ══
      else if(page==='P9B'){
        send(50,'Datos del cónyuge...');
        fi(PRE+'tbxSpouseSurname',g('q125_con_ap'));
        fi(PRE+'tbxSpouseGivenName',g('q126_con_nom'));
        const sd=gd('q127_con_dob');
        if(sd.day){se(PRE+'ddlDOBDay',sd.day);se(PRE+'ddlDOBMonth',sd.month,true);fi(PRE+'tbxDOBYear',sd.year);}
        se(PRE+'ddlSpouseNatDropDownList','DOMR');
        fi(PRE+'tbxSpousePOBCity',g('q128_con_pais_nac')||g('q10_ciudad_nac'));
        se(PRE+'ddlSpousePOBCountry','DOMR');
        se(PRE+'ddlSpouseAddressType','H');
      }

      // ══ P10 — TRABAJO ACTUAL ══
      else if(page==='P10'){
        send(20,'Ocupación...');
        const om={EMPLOYED:'B',STUDENT:'S','SELF-EMPLOYED':'F',RETIRED:'R',UNEMPLOYED:'U',HOMEMAKER:'H',OTHER:'O'};
        se(PRE+'ddlPresentOccupation',om[g('q131_ocupacion','EMPLOYED').toUpperCase()]||'B');
        await delay(400);
        send(45,'Datos del empleador...');
        fi(PRE+'tbxEmpSchName',g('q132_empleador')||'N/A');
        fi(PRE+'tbxEmpSchAddr1',g('q133_dir_emp1')||'N/A');
        fi(PRE+'tbxEmpSchAddr2','');
        fi(PRE+'tbxEmpSchCity',g('q134_emp_ciudad')||g('q25_ciudad'));
        const stE=g('q135_emp_prov');
        cb(PRE+'cbxWORK_EDUC_ADDR_STATE_NA',!stE);
        if(stE)fi(PRE+'tbxWORK_EDUC_ADDR_STATE',stE);
        const zpE=g('q137_emp_postal');
        cb(PRE+'cbxWORK_EDUC_ADDR_POSTAL_CD_NA',!zpE);
        if(zpE)fi(PRE+'tbxWORK_EDUC_ADDR_POSTAL_CD',zpE);
        fi(PRE+'tbxWORK_EDUC_TEL',g('q138_emp_tel')||g('q33_tel'));
        se(PRE+'ddlEmpSchCountry','DOMR');
        send(70,'Fecha inicio y salario...');
        const es=gd('q139_emp_inicio');
        if(es.day){se(PRE+'ddlEmpDateFromDay',es.day);se(PRE+'ddlEmpDateFromMonth',es.month,true);fi(PRE+'tbxEmpDateFromYear',es.year);}
        const sal=g('q140_salario');
        cb(PRE+'cbxCURR_MONTHLY_SALARY_NA',!sal);
        if(sal)fi(PRE+'tbxCURR_MONTHLY_SALARY',sal);
        ta(PRE+'tbxDescribeDuties',g('q141_funciones')||'Administrative and management duties');
      }

      // ══ P11 — EMPLEO ANTERIOR + EDUCACIÓN ══
      else if(page==='P11'){
        send(30,'Empleo anterior...');
        const rPE0=document.getElementById(PRE+'rblPreviouslyEmployed_0');
        const rPE1=document.getElementById(PRE+'rblPreviouslyEmployed_1');
        if(yn('q142_emp_ant')&&rPE0)rPE0.click(); else if(rPE1)rPE1.click();
        send(60,'Educación...');
        const rOE0=document.getElementById(PRE+'rblOtherEduc_0');
        const rOE1=document.getElementById(PRE+'rblOtherEduc_1');
        if(yn('q151_edu')&&rOE0)rOE0.click(); else if(rOE1)rOE1.click();
        if(yn('q151_edu')){
          await delay(300);
          fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolName',g('q152_escuela'));
          fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolAddr1',g('q153_escuela_dir')||g('q23_dir1'));
          fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolCity',g('q25_ciudad'));
          cb(PRE+'dtlPrevEduc_ctl00_cbxEDUC_INST_ADDR_STATE_NA',true);
          cb(PRE+'dtlPrevEduc_ctl00_cbxEDUC_INST_POSTAL_CD_NA',true);
          se(PRE+'dtlPrevEduc_ctl00_ddlSchoolCountry','DOMR');
          fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolCourseOfStudy',g('q154_carrera')||'Business Administration');
          const ef=gd('q155_edu_inicio');
          if(ef.day){se(PRE+'dtlPrevEduc_ctl00_ddlSchoolFromDay',ef.day);se(PRE+'dtlPrevEduc_ctl00_ddlSchoolFromMonth',ef.month,true);fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolFromYear',ef.year);}
          const et=gd('q156_edu_fin');
          if(et.day){se(PRE+'dtlPrevEduc_ctl00_ddlSchoolToDay',et.day);se(PRE+'dtlPrevEduc_ctl00_ddlSchoolToMonth',et.month,true);fi(PRE+'dtlPrevEduc_ctl00_tbxSchoolToYear',et.year);}
        }
      }

      // ══ P12 — INFORMACIÓN ADICIONAL ══
      else if(page==='P12'){
        send(20,'Clan/tribu — N...');
        const rCT1=document.getElementById(PRE+'rblCLAN_TRIBE_IND_1');if(rCT1)rCT1.click();
        send(35,'Idiomas...');
        fi(PRE+'dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME',g('q160_idiomas','Spanish'));
        send(50,'Países visitados — N...');
        const rCV1=document.getElementById(PRE+'rblCOUNTRIES_VISITED_IND_1');if(rCV1)rCV1.click();
        send(65,'Organizaciones — N...');
        const rOR1=document.getElementById(PRE+'rblORGANIZATION_IND_1');if(rOR1)rOR1.click();
        send(75,'Habilidades especiales — N...');
        const rSS1=document.getElementById(PRE+'rblSPECIALIZED_SKILLS_IND_1');if(rSS1)rSS1.click();
        send(85,'Servicio militar — N...');
        const rMS1=document.getElementById(PRE+'rblMILITARY_SERVICE_IND_1');if(rMS1)rMS1.click();
        send(92,'Grupos insurgentes — N...');
        const rIO1=document.getElementById(PRE+'rblINSURGENT_ORG_IND_1');if(rIO1)rIO1.click();
      }

      // ══ P13 — SEGURIDAD: SALUD ══
      else if(page==='P13'){
        send(30,'Enfermedad comunicable — N...');
        const rD1=document.getElementById(PRE+'rblDisease_1');if(rD1)rD1.click();
        send(60,'Trastorno mental — N...');
        const rDi1=document.getElementById(PRE+'rblDisorder_1');if(rDi1)rDi1.click();
        send(90,'Drogas — N...');
        const rDu1=document.getElementById(PRE+'rblDruguser_1');if(rDu1)rDu1.click();
      }

      // ══ P14 — SEGURIDAD: CRIMINAL ══
      else if(page==='P14'){
        send(10,'Preguntas criminales — todas N...');
        const sec14=['Arrested','ControlledSubstances','Prostitution','MoneyLaundering','HumanTrafficking','AssistedSevereTrafficking','HumanTraffickingRelated'];
        for(const n of sec14){
          const e=document.getElementById(PRE+'rbl'+n+'_1');
          if(e)e.click();
          await delay(60);
        }
      }

      // ══ P15 — SEGURIDAD: TERRORISMO ══
      else if(page==='P15'){
        send(10,'Preguntas terrorismo — todas N...');
        // Intentar todos los radios con valor N en esta página
        document.querySelectorAll('input[type="radio"][value="N"]').forEach(e=>{if(!e.checked)e.click();});
        await delay(200);
      }

      // ══ P16 — SEGURIDAD: OTRAS ══
      else if(page==='P16'){
        send(10,'Preguntas finales seguridad — todas N...');
        document.querySelectorAll('input[type="radio"][value="N"]').forEach(e=>{if(!e.checked)e.click();});
        await delay(200);
      }

      // ══ PÁGINA FINAL — PREPARADOR ══
      else if(page==='PFINAL'){
        send(50,'Idiomas y preparador...');
        fi(PRE+'tbxLangs',g('q160_idiomas','Spanish'));
        // No asistido — N
        document.querySelectorAll('input[type="radio"][value="N"]').forEach(e=>{if(e.id&&e.id.includes('Prepared')&&!e.checked)e.click();});
      }

      else{
        send(50,'Página no reconocida: '+page+' — llena manualmente');
      }

      send(100,'✅ Listo — avanzando...');
      await delay(800);
      clickNext();
      await delay(400);
      chrome.runtime.sendMessage({type:'done'});
    }catch(e){chrome.runtime.sendMessage({type:'error',msg:e.message});}
  }
  run();
}
