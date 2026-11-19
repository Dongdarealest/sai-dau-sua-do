/* Sai Đâu Sửa Đó: shared JS (progress v1 + SRS + safe storage).
   Mọi lần chạm localStorage/sessionStorage đều có try/catch + bộ nhớ tạm
   trong phiên, nên storage bị chặn cũng không giết trang (S-01). */
const DONE_KEY="sdsc-done-v2", PRAC_KEY="sdsc-practice-v2", STREAK_KEY="sdsc-streak-v1";
const PROGRESS_KEY="sdsc-progress-v1", PROGRESS_BAK=PROGRESS_KEY+".bak";
const CURRENT_VERSION=1;
let __mem={};
function storageGet(k){try{const v=localStorage.getItem(k);if(v!==null)return v;}catch(e){}return (k in __mem)?__mem[k]:null;}
function storageSet(k,v){try{localStorage.setItem(k,v);}catch(e){}try{__mem[k]=v;}catch(e2){}}
function storageRemove(k){try{localStorage.removeItem(k);}catch(e){}try{delete __mem[k];}catch(e2){}}
function sessionGet(k){try{const v=sessionStorage.getItem(k);if(v!==null)return v;}catch(e){}return (("s:"+k) in __mem)?__mem["s:"+k]:null;}
function sessionSet(k,v){try{sessionStorage.setItem(k,v);}catch(e){}try{__mem["s:"+k]=v;}catch(e2){}}
function todayISO(){const d=new Date();return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function isValidDateStr(s){if(typeof s!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;const d=new Date(s+"T00:00:00");return !isNaN(d.getTime())&&d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0")===s;}
function fmtDate(s){if(!isValidDateStr(s))return s;const p=s.split("-");return p[2]+"/"+p[1]+"/"+p[0];}
function dispDate(s){if(isValidDateStr(s))return fmtDate(s);return String(s||"").replace(/-/g,"/");}
function addDays(dateStr,n){const d=new Date(dateStr+"T00:00:00");d.setDate(d.getDate()+n);return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function yesterdayISO(){return addDays(todayISO(),-1);}
function emptyProgress(){return {version:1,updatedAt:new Date().toISOString(),lessons:{},practice:{},streak:{count:0,lastDate:"",dates:[]},review:{},history:[],settings:{dailyGoal:1,remindReview:true}};}
function normalizeProgress(o){
  const p=emptyProgress();
  if(o&&typeof o==="object"){
    if(o.lessons&&typeof o.lessons==="object")p.lessons=o.lessons;
    if(o.practice&&typeof o.practice==="object")p.practice=o.practice;
    if(o.review&&typeof o.review==="object")p.review=o.review;
    if(Array.isArray(o.history))p.history=o.history.slice(-500);
    if(o.streak&&typeof o.streak==="object"){p.streak.count=(typeof o.streak.count==="number"&&o.streak.count>=0)?o.streak.count:0;p.streak.lastDate=isValidDateStr(o.streak.lastDate)?o.streak.lastDate:"";p.streak.dates=Array.isArray(o.streak.dates)?o.streak.dates.filter(isValidDateStr).slice(-30):[];}
    if(o.settings&&typeof o.settings==="object"){p.settings.dailyGoal=(typeof o.settings.dailyGoal==="number"&&o.settings.dailyGoal>=1)?o.settings.dailyGoal:1;p.settings.remindReview=o.settings.remindReview!==false;}
  }
  const keys=Object.keys(p.practice).sort((a,b)=>String((p.practice[b]||{}).lastAt||"").localeCompare(String((p.practice[a]||{}).lastAt||""))).slice(0,1000);
  const pr={};keys.forEach(k=>{pr[k]=p.practice[k];});p.practice=pr;
  return p;
}
function migrateLegacy(p){
  let migrated=false;
  try{
    const rawDone=storageGet(DONE_KEY);
    if(rawDone){const done=JSON.parse(rawDone);if(done&&typeof done==="object"){
      Object.entries(done).forEach(([slug,date])=>{
        if(!isValidDateStr(date))return;
        const orphan=!(window.SDSC_LESSONS&&window.SDSC_LESSONS[slug]);
        p.lessons[slug]={done:true,doneAt:date,lastStudiedAt:date,selfGrade:null,reviews:0};
        if(orphan)p.lessons[slug].orphan=true;
        p.review[slug]={interval:1,nextDue:addDays(date,1),ease:2.5,reps:0};
        migrated=true;
      });
    }}
  }catch(e){}
  try{
    const rawPr=storageGet(PRAC_KEY);
    if(rawPr){const pr=JSON.parse(rawPr);if(pr&&typeof pr==="object"){
      Object.entries(pr).forEach(([key,v])=>{
        if(typeof v==="boolean"){p.practice[key]={choice:null,correct:v,attempts:1,lastAt:null};migrated=true;}
        else if(v&&typeof v==="object"&&typeof v.correct==="boolean"){p.practice[key]={choice:(v.choice===undefined?null:v.choice),correct:v.correct,attempts:(typeof v.attempts==="number"&&v.attempts>=1)?v.attempts:1,lastAt:v.lastAt||null};migrated=true;}
      });
    }}
  }catch(e){}
  try{
    const rawSt=storageGet(STREAK_KEY);
    if(rawSt){const st=JSON.parse(rawSt);if(st&&typeof st==="object"){
      const last=(typeof st.last==="string"&&isValidDateStr(st.last))?st.last:"";
      if(last){p.streak={count:(typeof st.streak==="number"&&st.streak>=1)?st.streak:1,lastDate:last,dates:[last]};migrated=true;}
    }}
  }catch(e){}
  if(migrated){
    p.history.push({date:todayISO(),at:new Date().toISOString(),slug:"",action:"import",note:"migrated from sdsc-done-v2/sdsc-practice-v2/sdsc-streak-v1"});
  }
  return migrated;
}
let __progressCache=null;
function loadProgress(){
  if(__progressCache)return __progressCache;
  let raw=null;try{raw=storageGet(PROGRESS_KEY);}catch(e){}
  if(raw){
    try{const o=JSON.parse(raw);if(!o||typeof o!=="object"||o.version!==CURRENT_VERSION)throw new Error("bad version");__progressCache=normalizeProgress(o);return __progressCache;}
    catch(e){
      try{const bak=storageGet(PROGRESS_BAK);if(bak){const o2=JSON.parse(bak);if(o2&&typeof o2==="object"&&o2.version===CURRENT_VERSION){try{storageSet(PROGRESS_KEY+".corrupt."+Date.now(),raw);}catch(e2){}__progressCache=normalizeProgress(o2);return __progressCache;}}}catch(e2){}
      try{storageSet(PROGRESS_KEY+".corrupt."+Date.now(),raw);}catch(e2){}
      __progressCache=emptyProgress();return __progressCache;
    }
  }
  const p=emptyProgress();
  if(migrateLegacy(p))saveProgress(p);
  __progressCache=p;return p;
}
function getProgress(){return loadProgress();}
function saveProgress(p){
  try{p.updatedAt=new Date().toISOString();}catch(e){}
  try{if(Array.isArray(p.history))p.history=p.history.slice(-500);}catch(e){}
  try{
    const raw=JSON.stringify(p);
    storageSet(PROGRESS_BAK,raw);
    storageSet(PROGRESS_KEY,raw);
  }catch(e){}
  __progressCache=p;
}
function updateProgress(fn){const p=getProgress();try{fn(p);}catch(e){}saveProgress(p);return p;}
function srsNew(todayStr){return {interval:1,nextDue:addDays(todayStr,1),ease:2.5,reps:0};}
function srsUpdate(r,grade,todayStr){
  r=r||{interval:1,ease:2.5,reps:0};
  if(grade==="kho"){r.interval=1;r.ease=Math.max(1.3,Math.round((r.ease-0.2)*100)/100);r.reps=0;}
  else if(grade==="vua"){r.interval=Math.max(1,Math.round(r.interval*r.ease));r.reps=(r.reps||0)+1;}
  else{r.interval=Math.max(1,Math.round(r.interval*r.ease*1.3));r.ease=Math.min(2.5,Math.round((r.ease+0.1)*100)/100);r.reps=(r.reps||0)+1;}
  r.interval=Math.min(60,Math.max(1,r.interval));
  r.nextDue=addDays(todayStr,r.interval);
  return r;
}
function pushHistory(p,entry){try{p.history.push(entry);if(p.history.length>500)p.history=p.history.slice(-500);}catch(e){}}
function updateStreakIn(p,todayStr){
  const st=p.streak||{count:0,lastDate:"",dates:[]};
  if(st.lastDate===todayStr)return st;
  if(st.lastDate===addDays(todayStr,-1)){st.count=(st.count||0)+1;}else{st.count=1;}
  st.lastDate=todayStr;
  st.dates=st.dates||[];if(!st.dates.includes(todayStr))st.dates.push(todayStr);
  st.dates=st.dates.filter(isValidDateStr).sort().slice(-30);
  p.streak=st;return st;
}
function loadJSON(k){try{const v=storageGet(k);return v?JSON.parse(v)||{}:{};}catch(e){return{};}}
function saveJSON(k,v){try{storageSet(k,JSON.stringify(v));}catch(e){}}
function loadStreak(){const p=getProgress();return {streak:p.streak.count||0,last:p.streak.lastDate||""};}
function updateStreak(){const p=getProgress();const t=todayISO();updateStreakIn(p,t);saveProgress(p);return loadStreak();}
const ICON_MOON='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
const ICON_SUN='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
function syncThemeBtn(){try{const b=document.getElementById("theme-toggle");if(b)b.innerHTML=document.documentElement.dataset.theme==="dark"?ICON_SUN:ICON_MOON;}catch(e){}}
(function(){try{const t=storageGet("sdsc-theme");if(t){document.documentElement.dataset.theme=t;}else if(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches){document.documentElement.dataset.theme="dark";}}catch(e){}syncThemeBtn();})();
document.addEventListener("click",e=>{try{const b=e.target.closest("#theme-toggle");if(!b)return;const cur=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=cur;storageSet("sdsc-theme",cur);syncThemeBtn();}catch(err){}});
let __voices=[];
function loadVoices(){try{__voices=speechSynthesis.getVoices()||[];}catch(e){__voices=[];}}
try{if("speechSynthesis" in window){loadVoices();speechSynthesis.addEventListener("voiceschanged",loadVoices);}}catch(e){}
function speak(text,btn){
  if(!("speechSynthesis" in window)){if(btn){const old=btn.textContent;btn.textContent="Không có giọng đọc";setTimeout(()=>{btn.textContent=old;},2000);}return;}
  try{speechSynthesis.cancel();}catch(e){}
  const u=new SpeechSynthesisUtterance(text);u.lang="en-US";u.rate=0.9;
  if(!__voices.length)loadVoices();
  const v=__voices.find(v=>v.lang&&v.lang.toLowerCase().startsWith("en-us"));
  if(v)u.voice=v;
  if(btn){btn.classList.add("playing");const clear=()=>btn.classList.remove("playing");u.onend=clear;u.onerror=clear;setTimeout(clear,15000);}
  try{speechSynthesis.speak(u);}catch(e){if(btn)btn.classList.remove("playing");}
}
document.addEventListener("click",e=>{
  const b=e.target.closest(".listen");if(!b)return;
  speak(b.dataset.say,b);
});
function escapeHtml(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");}
function savePracticeResult(key,choice,correct){
  updateProgress(p=>{
    const old=p.practice[key]||{};
    p.practice[key]={choice:choice,correct:!!correct,attempts:(typeof old.attempts==="number"?old.attempts:0)+1,lastAt:new Date().toISOString()};
    pushHistory(p,{date:todayISO(),at:new Date().toISOString(),slug:key.split(":")[0],action:"practice",key:key,correct:!!correct});
  });
}
function gradeWidget(box,choice){
  const answer=parseInt(box.dataset.answer,10);
  const explain=box.dataset.explain||"";
  const key=box.dataset.key;
  const r=box.querySelector(".grade-result");
  if(isNaN(answer)){
    if(r){r.style.display="block";r.className="grade-result bad";r.innerHTML="<b>Không chấm được câu này</b> (thiếu đáp án, báo cho trang nhé).";}
    return;
  }
  box.querySelectorAll(".opt").forEach((o,i)=>{
    o.disabled=true;
    if(i===answer)o.classList.add("correct");
    if(i===choice&&choice!==answer)o.classList.add("wrong-pick");
  });
  /* S-02: hiện kết quả TRƯỚC, ghi storage sau. Ghi lỗi vẫn hiện kết quả. */
  if(r){
    r.style.display="block";
    r.className="grade-result "+(choice===answer?"good":"bad");
    r.innerHTML=(choice===answer?"<b>Đúng rồi</b> ":"<b>Chưa đúng: đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(explain);
  }
  try{savePracticeResult(key,choice,choice===answer);}catch(e){}
  if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="block";}
  updatePracticeScore();
}
function restoreGrade(box){
  const key=box.dataset.key;
  const saved=getProgress().practice[key];
  if(!saved||typeof saved.correct!=="boolean")return;
  const answer=parseInt(box.dataset.answer,10);
  if(isNaN(answer))return;
  box.querySelectorAll(".opt").forEach((o,i)=>{o.disabled=true;if(i===answer)o.classList.add("correct");if(saved.choice!==null&&saved.choice!==undefined&&i===saved.choice&&saved.choice!==answer)o.classList.add("wrong-pick");});
  const r=box.querySelector(".grade-result");
  if(r){
    r.style.display="block";
    r.className="grade-result "+(saved.correct?"good":"bad");
    if(saved.choice===null||saved.choice===undefined){r.innerHTML=(saved.correct?"<b>Bạn đã làm đúng (trước đây)</b> ":"<b>Bạn đã làm trước đây, đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(box.dataset.explain||"");}
    else{r.innerHTML=(saved.correct?"<b>Bạn đã làm đúng</b> ":"<b>Bạn đã làm, đáp án là "+String.fromCharCode(65+answer)+"</b> ")+escapeHtml(box.dataset.explain||"");}
  }
  if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="block";}
}
document.querySelectorAll(".grade").forEach(box=>{
  const key=box.dataset.key;
  box.querySelectorAll(".opt").forEach(o=>o.addEventListener("click",()=>gradeWidget(box,parseInt(o.dataset.i,10))));
  try{restoreGrade(box);}catch(e){}
  const retry=box.querySelector(".grade-retry");
  if(retry)retry.addEventListener("click",()=>{
    try{updateProgress(p=>{delete p.practice[key];});}catch(e){}
    const rr=box.querySelector(".grade-result");if(rr)rr.style.display="none";
    box.querySelectorAll(".opt").forEach(o=>{o.disabled=false;o.classList.remove("correct","wrong-pick");});
    if(key.endsWith(":q")){const reveal=document.getElementById("answer-box");if(reveal)reveal.style.display="none";}
    updatePracticeScore();
  });
});
/* ---- word_order: xếp từ thành câu ---- */
function initWordOrder(box){
  const key=box.dataset.key;
  let answer=[];try{answer=JSON.parse(box.dataset.answer||"[]");}catch(e){answer=[];}
  let options=[];try{options=JSON.parse(box.dataset.options||"[]");}catch(e){options=[];}
  const pickedEl=box.querySelector(".wo-picked"), chipsEl=box.querySelector(".wo-chips"),
        resultEl=box.querySelector(".grade-result"), ansEl=box.querySelector(".wo-answer"),
        checkBtn=box.querySelector(".wo-check"), retryBtn=box.querySelector(".wo-retry");
  let picked=[];
  function renderPicked(){
    pickedEl.innerHTML=picked.map(i=>'<button type="button" class="wo-chip picked" data-i="'+i+'">'+escapeHtml(options[i]!==undefined?options[i]:"")+'</button>').join("")||'<span class="wo-empty">Bấm các từ bên dưới theo đúng thứ tự…</span>';
    pickedEl.querySelectorAll(".wo-chip").forEach(b=>b.addEventListener("click",()=>{
      const idx=parseInt(b.dataset.i,10);picked=picked.filter(x=>x!==idx);
      const chip=chipsEl.querySelector('[data-i="'+idx+'"]');if(chip)chip.disabled=false;
      renderPicked();
    }));
  }
  function correctSentence(){return answer.map(i=>options[i]).join(" ").replace(/ ([?.!,])/g,"$1");}
  function showResult(correct){
    if(resultEl){resultEl.style.display="block";resultEl.className="grade-result "+(correct?"good":"bad");
      resultEl.innerHTML=(correct?"<b>Đúng rồi</b> ":"<b>Chưa đúng: câu đúng là:</b> ")+escapeHtml(box.dataset.explain||"");}
    if(ansEl){ansEl.style.display="block";ansEl.textContent="Câu đúng: "+correctSentence();}
  }
  chipsEl.querySelectorAll(".wo-chip").forEach(ch=>{
    ch.addEventListener("click",()=>{
      if(ch.disabled)return;
      const idx=parseInt(ch.dataset.i,10);
      picked.push(idx);ch.disabled=true;renderPicked();
    });
  });
  if(checkBtn)checkBtn.addEventListener("click",()=>{
    if(!picked.length)return;
    const correct=picked.length===answer.length&&picked.every((v,i)=>v===answer[i]);
    chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=true;});
    showResult(correct);
    try{savePracticeResult(key,picked.slice(),correct);}catch(e){}
    updatePracticeScore();
  });
  if(retryBtn)retryBtn.addEventListener("click",()=>{
    picked=[];renderPicked();
    chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=false;});
    if(resultEl)resultEl.style.display="none";
    if(ansEl)ansEl.style.display="none";
    try{updateProgress(p=>{delete p.practice[key];});}catch(e){}
    updatePracticeScore();
  });
  try{
    const saved=getProgress().practice[key];
    if(saved&&typeof saved.correct==="boolean"&&Array.isArray(saved.choice)){
      picked=saved.choice.slice();renderPicked();
      chipsEl.querySelectorAll(".wo-chip").forEach(c=>{c.disabled=true;});
      showResult(saved.correct);
    }else{renderPicked();}
  }catch(e){renderPicked();}
}
document.querySelectorAll(".grade-wo").forEach(initWordOrder);
function practiceTotalsFor(slug){
  const p=getProgress();
  let total=0,done=0,right=0;
  const totals=(window.SDSC_TOTALS||{});
  total=totals[slug]||0;
  Object.entries(p.practice||{}).forEach(([k,v])=>{
    if(k===slug+":q"||k.indexOf(slug+":")===0){done++;if(v&&v.correct)right++;}
  });
  return {right: right,total: total,done: done};
}
function updatePracticeScore(){
  let siteRight=0,siteDone=0;
  try{const p=getProgress();Object.values(p.practice||{}).forEach(v=>{siteDone++;if(v&&v.correct)siteRight++;});}catch(e){}
  const siteTotal=window.SDSC_TOTAL_GRADED||0;
  document.querySelectorAll(".practice-score-num").forEach(el=>{
    const slug=el.dataset.slug;
    if(slug){const t=practiceTotalsFor(slug);el.textContent=t.right+" / "+t.total+" câu đúng ("+t.done+" đã làm), bài này";}
    else{el.textContent=siteRight+" / "+siteTotal+" câu đúng ("+siteDone+" đã làm), toàn trang";}
  });
  document.querySelectorAll(".practice-site-num").forEach(el=>{el.textContent=siteRight+" / "+siteTotal+" câu đúng ("+siteDone+" đã làm)";});
}
updatePracticeScore();
window.addEventListener("storage",e=>{
  if(e&&e.key===PROGRESS_KEY){try{__progressCache=null;loadProgress();}catch(err){}try{if(window.__sdscRenderProgress)window.__sdscRenderProgress();}catch(err){}try{updatePracticeScore();}catch(err){}}
});
/* ---- xuất / nhập tiến độ (§2.3) ---- */
function validImportDate(s){if(!isValidDateStr(s))return false;const d=new Date(s+"T00:00:00");const max=new Date();max.setDate(max.getDate()+1);max.setHours(23,59,59,999);return d.getTime()<=max.getTime();}
function validImportNextDue(s){if(!isValidDateStr(s))return false;const d=new Date(s+"T00:00:00");const max=new Date();max.setDate(max.getDate()+60);max.setHours(23,59,59,999);return d.getTime()<=max.getTime();}
function validateImportFile(text){
  let obj;
  try{obj=JSON.parse(text);}catch(e){return {ok:false,error:"File không phải JSON hợp lệ (lỗi ở ký tự "+(e&&e.message?e.message:"không rõ")+"). Kiểm tra lại file đã tải về."};}
  if(!obj||typeof obj!=="object"||obj.app!=="sai-dau-sua-do"||obj.kind!=="progress-export"){return {ok:false,error:"Đây không phải file tiến độ của Sai Đâu Sửa Đó (thiếu app/kind đúng)."};}
  const data=obj.data;
  if(!data||typeof data!=="object")return {ok:false,error:"Trường 'data' phải là object, nhận được "+(Array.isArray(data)?"array":typeof data)+"."};
  if(typeof data.version!=="number"||!Number.isInteger(data.version))return {ok:false,error:"File được xuất từ phiên bản không hỗ trợ (version không hợp lệ)."};
  if(data.version>CURRENT_VERSION)return {ok:false,error:"File được xuất từ phiên bản mới hơn (v"+data.version+"), trang này mới hỗ trợ tới v"+CURRENT_VERSION+". Cập nhật trang rồi nhập lại."};
  if(data.version<1)return {ok:false,error:"Không chuyển đổi được dữ liệu cũ (v"+data.version+"): phiên bản quá cũ."};
  const lessons=(window.SDSC_LESSONS||{});
  const badSlug=[];
  function checkSlug(s){if(!s||typeof s!=="string")return false;if(lessons[s])return true;return /^[a-z0-9-]+$/.test(s);}
  ["lessons","practice","review"].forEach(f=>{if(data[f]!==undefined&&(!data[f]||typeof data[f]!=="object"||Array.isArray(data[f])))return;});
  if(data.lessons!==undefined&&(!data.lessons||typeof data.lessons!=="object"||Array.isArray(data.lessons)))return {ok:false,error:"Trường 'lessons' phải là object, nhận được "+(Array.isArray(data.lessons)?"array":typeof data.lessons)+"."};
  if(data.practice!==undefined&&(!data.practice||typeof data.practice!=="object"||Array.isArray(data.practice)))return {ok:false,error:"Trường 'practice' phải là object, nhận được "+(Array.isArray(data.practice)?"array":typeof data.practice)+"."};
  if(data.review!==undefined&&(!data.review||typeof data.review!=="object"||Array.isArray(data.review)))return {ok:false,error:"Trường 'review' phải là object, nhận được "+(Array.isArray(data.review)?"array":typeof data.review)+"."};
  if(data.history!==undefined&&!Array.isArray(data.history))return {ok:false,error:"Trường 'history' phải là array, nhận được "+typeof data.history+"."};
  if(data.streak!==undefined&&(!data.streak||typeof data.streak!=="object"||Array.isArray(data.streak)))return {ok:false,error:"Trường 'streak' phải là object, nhận được "+(Array.isArray(data.streak)?"array":typeof data.streak)+"."};
  const slugs=new Set([...Object.keys(data.lessons||{}),...Object.keys(data.review||{})]);
  slugs.forEach(s=>{if(!checkSlug(s))badSlug.push(s);});
  if(badSlug.length)return {ok:false,error:"Bài '"+badSlug.slice(0,5).join("', '")+"' trong file không có trên trang. Có thể file thuộc bản web khác."};
  const dateFields=[];
  Object.entries(data.lessons||{}).forEach(([slug,v])=>{if(v&&typeof v==="object"){["doneAt","lastStudiedAt"].forEach(f=>{if(v[f]!==undefined&&v[f]!==null)dateFields.push([slug,v[f]]);});}});
  Object.entries(data.review||{}).forEach(([slug,v])=>{if(v&&typeof v==="object"&&v.nextDue)dateFields.push([slug,v.nextDue,true]);});
  if(data.streak&&data.streak.lastDate)dateFields.push(["",data.streak.lastDate,false]);
  for(const [slug,val,isDue] of dateFields){const okD=isDue?validImportNextDue(val):validImportDate(val);if(!okD)return {ok:false,error:isDue?("Ngày ôn lại '"+dispDate(val)+"' ở bài "+slug+" quá xa trong tương lai (tối đa 60 ngày tới)."):("Ngày '"+dispDate(val)+"' ở bài "+(slug||"chuỗi học")+" không phải ngày hợp lệ.")};}
  for(const [slug,v] of Object.entries(data.lessons||{})){
    if(!v||typeof v!=="object")continue;
    if(v.selfGrade!==undefined&&v.selfGrade!==null&&["kho","vua","de"].indexOf(v.selfGrade)<0)return {ok:false,error:"Bài "+slug+": selfGrade phải là kho/vua/de hoặc null, nhận được "+JSON.stringify(v.selfGrade)+"."};
    if(v.reviews!==undefined&&(typeof v.reviews!=="number"||!Number.isInteger(v.reviews)||v.reviews<0))return {ok:false,error:"Bài "+slug+": reviews phải là số nguyên ≥ 0."};
  }
  for(const [slug,v] of Object.entries(data.review||{})){
    if(!v||typeof v!=="object")continue;
    if(typeof v.interval!=="number"||!Number.isInteger(v.interval)||v.interval<1||v.interval>60)return {ok:false,error:"Bài "+slug+": interval phải từ 1 tới 60, nhận được "+v.interval+"."};
    if(typeof v.ease!=="number"||v.ease<1.3||v.ease>2.5)return {ok:false,error:"Bài "+slug+": ease phải từ 1.3 tới 2.5, nhận được "+v.ease+"."};
    if(typeof v.reps!=="number"||!Number.isInteger(v.reps)||v.reps<0)return {ok:false,error:"Bài "+slug+": reps phải là số nguyên ≥ 0."};
    if(!validImportNextDue(v.nextDue))return {ok:false,error:"Ngày ôn lại '"+dispDate(v.nextDue)+"' ở bài "+slug+" quá xa trong tương lai (tối đa 60 ngày tới)."};
  }
  for(const [k,v] of Object.entries(data.practice||{})){
    if(!v||typeof v!=="object"||typeof v.correct!=="boolean")return {ok:false,error:"Câu luyện '"+k+"': phải có trường correct (true/false)."};
    if(typeof v.attempts!=="number"||!Number.isInteger(v.attempts)||v.attempts<1)return {ok:false,error:"Câu luyện '"+k+"': attempts phải là số nguyên ≥ 1."};
  }
  if(data.streak&&typeof data.streak.count!=="undefined"&&(typeof data.streak.count!=="number"||!Number.isInteger(data.streak.count)||data.streak.count<0))return {ok:false,error:"Trường 'streak.count' phải là số nguyên ≥ 0."};
  if(Array.isArray(data.history)){for(const h of data.history){if(!h||typeof h!=="object"||["done","undone","practice","review","self-grade","import","reset","migrate"].indexOf(h.action)<0)return {ok:false,error:"Trường 'history[].action' không hợp lệ: "+JSON.stringify(h&&h.action)+"."};}}
  for(const [slug,v] of Object.entries(data.review||{})){
    const L=(data.lessons||{})[slug];
    if(!L||L.done!==true)return {ok:false,error:"Bài "+slug+" có lịch ôn nhưng chưa được đánh dấu đã nhớ."};
    if(L.doneAt&&v.nextDue&&v.nextDue<L.doneAt)return {ok:false,error:"Bài "+slug+": nextDue ("+dispDate(v.nextDue)+") phải từ ngày đánh dấu đã nhớ ("+dispDate(L.doneAt)+") trở đi."};
  }
  if(data.streak&&Array.isArray(data.streak.dates)&&data.streak.dates.length&&data.streak.lastDate){
    const last=[...data.streak.dates].sort().pop();
    if(last!==data.streak.lastDate)return {ok:false,error:"Chuỗi học không nhất quán: lastDate phải là ngày cuối trong danh sách ngày học."};
  }
  if(text.length>1024*1024)return {ok:false,error:"File quá lớn (hơn 1 MB). Có thể đây không phải file tiến độ."};
  if(Array.isArray(data.history)&&data.history.length>5000)return {ok:false,error:"File quá lớn (hơn 1 MB). Có thể đây không phải file tiến độ."};
  return {ok:true,data:normalizeProgress(data)};
}
function mergeProgress(current,incoming){
  const out=JSON.parse(JSON.stringify(current));
  Object.entries(incoming.lessons||{}).forEach(([slug,v])=>{
    const cur=out.lessons[slug];
    const newDate=v.lastStudiedAt||v.doneAt||"", curDate=cur?(cur.lastStudiedAt||cur.doneAt||""):"";
    if(!cur||newDate>=curDate){out.lessons[slug]=v;if(incoming.review&&incoming.review[slug])out.review[slug]=incoming.review[slug];}
  });
  Object.entries(incoming.practice||{}).forEach(([k,v])=>{
    const cur=out.practice[k];
    if(!cur||String(v.lastAt||"")>=String(cur.lastAt||""))out.practice[k]=v;
  });
  const allDates=new Set([...(out.streak.dates||[]),...((incoming.streak||{}).dates||[])]);
  out.streak.dates=[...allDates].filter(isValidDateStr).sort().slice(-30);
  const curLast=out.streak.lastDate||"", incLast=(incoming.streak||{}).lastDate||"";
  if(incLast>curLast){out.streak.count=incoming.streak.count||out.streak.count;out.streak.lastDate=incLast;}
  else if(out.streak.dates.length){out.streak.lastDate=[...out.streak.dates].sort().pop();}
  out.history=[...(out.history||[]),...((incoming.history||[]))].sort((a,b)=>String(a.at||"").localeCompare(String(b.at||""))).slice(-500);
  return out;
}
function exportProgress(){
  const p=getProgress();
  const env={app:"sai-dau-sua-do",kind:"progress-export",version:1,exportedAt:new Date().toISOString(),data:p};
  try{
    const blob=new Blob([JSON.stringify(env,null,2)],{type:"application/json"});
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);
    a.download="sai-dau-sua-do-tien-do-"+todayISO()+".json";a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),5000);
    return true;
  }catch(e){return false;}
}
function importProgressText(text,mode){
  const v=validateImportFile(text);
  if(!v.ok)return v;
  const incoming=v.data;
  let result;
  if(mode==="overwrite"){result=incoming;}
  else{result=mergeProgress(getProgress(),incoming);}
  updateProgress(p=>{Object.keys(p).forEach(k=>{delete p[k];});Object.assign(p,JSON.parse(JSON.stringify(result)));pushHistory(p,{date:todayISO(),at:new Date().toISOString(),slug:"",action:"import",note:"mode="+(mode==="overwrite"?"overwrite":"merge")});});
  const doneCount=Object.values(result.lessons||{}).filter(l=>l&&l.done).length;
  const pracCount=Object.keys(result.practice||{}).length;
  const streakCount=(result.streak&&result.streak.count)||0;
  return {ok:true,message:"Đã nhập: "+doneCount+" bài đã nhớ, "+pracCount+" câu luyện, chuỗi "+streakCount+" ngày (chế độ "+(mode==="overwrite"?"Ghi đè":"Gộp")+")."};
}
function loadSpeaking(){
  try{const v=storageGet("sdsc-speaking-v1");const d=v?JSON.parse(v):null;if(d&&typeof d==="object")return {sessions:d.sessions||0,minutes:d.minutes||0,words:d.words||0,best:d.best||0,lastDay:d.lastDay||""};}catch(e){}
  return {sessions:0,minutes:0,words:0,best:0,lastDay:""};
}
function speakingHoursText(mins){
  mins=Math.round(mins||0);
  if(mins<60)return mins+" phút";
  const h=Math.floor(mins/60);const m=mins%60;
  return h+" giờ"+(m?" "+m+" phút":"");
}
function recordSpeaking(minutes,words,score){
  if(!isFinite(minutes)||minutes<=0)return;
  const d=loadSpeaking();
  d.sessions=(d.sessions||0)+1;
  d.minutes=Math.round(((d.minutes||0)+minutes)*10)/10;
  d.words=(d.words||0)+(words||0);
  if(typeof score==="number"&&score>0)d.best=Math.max(d.best||0,Math.round(score));
  d.lastDay=todayISO();
  try{storageSet("sdsc-speaking-v1",JSON.stringify(d));}catch(e){}
  try{noteSpeakingSession(d.minutes);}catch(e){}
}
/* Điền tổng số bài vào header (tối ưu B 19/11): tổng số lấy từ data.js
   lúc chạy, không ghi cứng vào HTML, để thêm bài mới không đổi mọi trang.
   Trang chủ và trang lộ trình cũng tự cập nhật lại đúng số này sau đó. */
(function(){
  try{
    var total=window.SDSC_TOTAL_LESSONS||0;
    document.querySelectorAll(".total-lessons-num").forEach(function(el){el.textContent=total;});
    var p=getProgress();
    var n=Object.entries(p.lessons||{}).filter(function(le){var l=le[1];return l&&l.done&&window.SDSC_LESSONS[le[0]];}).length;
    document.querySelectorAll(".progress-num").forEach(function(el){el.textContent=n+" / "+total+" bài";});
  }catch(e){}
})();
