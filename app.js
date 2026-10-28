'use strict';
(() => {
  const data = window.POLL_DATA;
  const $ = id => document.getElementById(id);
  if (!data?.records?.length) { $('coverage').textContent = '검증된 조사 데이터가 아직 없습니다.'; return; }
  const rows = data.records;
  const series = [
    {id:'CATI-approve',method:'CATI',key:'approve',label:'전화면접 · 긍정',color:'#187d8d'},
    {id:'CATI-disapprove',method:'CATI',key:'disapprove',label:'전화면접 · 부정',color:'#cb583f'},
    {id:'ARS-approve',method:'ARS',key:'approve',label:'ARS · 긍정',color:'#187d8d'},
    {id:'ARS-disapprove',method:'ARS',key:'disapprove',label:'ARS · 부정',color:'#cb583f'}
  ];
  const active = new Set(series.map(s=>s.id));
  const date = s => new Date(s+'T00:00:00Z');
  const fmt = s => s.replaceAll('-','.');
  const short = s => s.slice(5).replace('-','.');
  const methodName = m => m==='CATI'?'전화면접':'ARS';
  const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num = n => Number(n).toFixed(1);
  const signed = n => (n>0?'+':'')+num(n);
  const delta = (r,key) => {
    const list=rows.filter(x=>x.method===r.method && x.endDate<r.endDate);
    const prev=list.at(-1);
    return prev?`<b>${signed(r[key]-prev[key])}%p</b> <span>직전 ${short(prev.endDate)} 대비</span>`:'첫 수록 조사';
  };
  let period='all', visible=[], dates=[], selected='', width=0;
  const latestEnd=rows.at(-1).endDate;
  $('coverage').textContent=`수록 ${fmt(rows[0].endDate)} — ${fmt(latestEnd)}`;
  $('updated').textContent=`자료 확인·반영 ${fmt(data.collectedAt)}`;
  $('latest-date').textContent=`조사 종료 ${fmt(latestEnd)} 기준`;
  $('latest-cards').innerHTML=['CATI','ARS'].map(m=>{
    const r=rows.filter(x=>x.method===m).at(-1);
    if(!r)return '';
    return `<article class="latest-card"><div class="card-top"><div class="method-name"><span class="swatch ${m==='ARS'?'ars':''}"></span>${methodName(m)} <span class="method-en">${m==='CATI'?'CATI':'자동응답'}</span></div><span class="date-small">${fmt(r.startDate)}–${short(r.endDate)}</span></div><div class="metrics">${[['approve','긍정','positive'],['disapprove','부정','negative']].map(([key,label,cls])=>`<div class="metric ${cls}"><span class="label">${label} 평가</span><strong>${num(r[key])}<small>%</small></strong><span class="delta">${delta(r,key)}</span></div>`).join('')}</div></article>`;
  }).join('');
  $('legend').innerHTML=series.map(s=>`<button data-series="${s.id}" aria-pressed="true"><span class="swatch ${s.method==='ARS'?'ars':''}" style="color:${s.color}"></span>${s.label}</button>`).join('');
  $('legend').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const id=b.dataset.series;active.has(id)?active.delete(id):active.add(id);b.setAttribute('aria-pressed',String(active.has(id)));draw();});
  document.querySelectorAll('[data-period]').forEach(b=>b.addEventListener('click',()=>{
    period=b.dataset.period;
    document.querySelectorAll('[data-period]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
    updatePeriod();
  }));
  function updatePeriod(){
    const cutoff=date(latestEnd);
    if(period!=='all')cutoff.setUTCMonth(cutoff.getUTCMonth()-Number(period));
    visible=rows.filter(r=>period==='all'||date(r.endDate)>=cutoff);
    dates=[...new Set(visible.map(r=>r.endDate))];
    if(!dates.includes(selected))selected=dates.at(-1);
    $('timeline').max=String(dates.length-1);
    $('timeline').value=String(dates.indexOf(selected));
    $('range-label').textContent=`${fmt(dates[0])} — ${fmt(dates.at(-1))}`;
    renderSelection();renderInsights();draw();
  }
  function choose(index){
    index=Math.max(0,Math.min(dates.length-1,index));selected=dates[index];$('timeline').value=String(index);
    renderSelection();draw();
  }
  $('timeline').addEventListener('input',e=>choose(Number(e.target.value)));
  $('prev').addEventListener('click',()=>choose(dates.indexOf(selected)-1));
  $('next').addEventListener('click',()=>choose(dates.indexOf(selected)+1));
  function renderSelection(){
    const idx=dates.indexOf(selected);
    $('prev').disabled=idx===0;$('next').disabled=idx===dates.length-1;
    $('timeline').setAttribute('aria-valuetext',fmt(selected)+' 조사 종료');
    const pair=visible.filter(r=>r.endDate===selected);
    $('selection').innerHTML=`<div class="selection-heading"><h3>${fmt(selected)} <span style="font-weight:400">조사 종료</span></h3><span>${idx+1} / ${dates.length}개 시점</span></div><div class="selection-grid">${['CATI','ARS'].map(m=>{
      const r=pair.find(x=>x.method===m);
      if(!r)return `<article><h4>${methodName(m)}</h4><p class="unpaired">이 종료일에 수록된 조사가 없습니다.</p></article>`;
      return `<article><div class="detail-top"><h4>${methodName(m)}</h4><span class="method-en">등록 ${esc(r.registration)}</span></div><p class="detail-values"><span class="positive">긍정 <b>${num(r.approve)}</b>%</span> <span class="negative">부정 <b>${num(r.disapprove)}</b>%</span><span class="other">모름·무응답 ${num(r.unknown)}%</span></p><p class="detail-meta">조사 ${fmt(r.startDate)}–${short(r.endDate)} · 공표 ${fmt(r.publishedDate)}<br>${esc(r.target)} ${r.sampleSize.toLocaleString('ko-KR')}명<br>${esc(r.margin)} · 응답률 ${esc(r.responseRate)}<br>조사·의뢰: ${esc(r.agency)} · ${esc(r.frame)}</p><details><summary class="question">질문 문구 보기</summary><p class="question">${esc(r.question)}</p></details><div class="links"><a href="${esc(r.sourceUrl)}" target="_blank" rel="noopener noreferrer">등록자료 ↗</a><a href="${esc(r.pdfUrl)}" target="_blank" rel="noopener noreferrer">결과표 원문 · ${r.pdfPage}쪽 ↗</a></div></article>`;
    }).join('')}</div>`;
  }
  function renderInsights(){
    const c=visible.filter(r=>r.method==='CATI'),a=visible.filter(r=>r.method==='ARS');
    const lastC=c.at(-1),lastA=a.at(-1);
    const common=[...dates].reverse().find(d=>visible.some(r=>r.endDate===d&&r.method==='CATI')&&visible.some(r=>r.endDate===d&&r.method==='ARS'));
    const paired=visible.filter(r=>r.endDate===common);
    const pc=paired.find(r=>r.method==='CATI'),pa=paired.find(r=>r.method==='ARS');
    const gap=pc&&pa?pc.approve-pa.approve:null;
    const articles=[
      {title:'전화면접 · 기간 내 긍정 변화',value:c.length>1?signed(lastC.approve-c[0].approve):'—',unit:'%p',text:c.length>1?`${fmt(c[0].endDate)} ${num(c[0].approve)}% → ${fmt(lastC.endDate)} ${num(lastC.approve)}%`:'비교 가능한 조사가 부족합니다.'},
      {title:'ARS · 기간 내 긍정 변화',value:a.length>1?signed(lastA.approve-a[0].approve):'—',unit:'%p',text:a.length>1?`${fmt(a[0].endDate)} ${num(a[0].approve)}% → ${fmt(lastA.endDate)} ${num(lastA.approve)}%`:'비교 가능한 조사가 부족합니다.'},
      {title:'최근 동일 종료일 · 긍정 격차',value:gap===null?'—':num(Math.abs(gap)),unit:'%p',text:gap===null?'동일 종료일의 조사 쌍이 없습니다.':`${fmt(common)} 종료 조사. ${gap===0?'두 방식의 수치가 같습니다.':`${gap>0?'전화면접':'ARS'} 수치가 높습니다.`} 조사 기간은 상세에서 확인하세요.`}
    ];
    $('insights').innerHTML=articles.map(x=>`<article class="insight"><h3>${x.title}</h3><strong>${x.value}<small>${x.unit}</small></strong><p>${x.text}</p></article>`).join('');
  }
  const NS='http://www.w3.org/2000/svg';
  function element(tag,attrs,parent,text){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));if(text!=null)e.textContent=text;parent.append(e);return e;}
  function draw(){
    const svg=$('chart');
    svg.querySelectorAll('g').forEach(g=>g.remove());
    width=$('plot').clientWidth;
    const mobile=width<560,H=mobile?315:390,L=mobile?29:36,R=mobile?10:20,T=22,B=32;
    svg.setAttribute('viewBox',`0 0 ${width} ${H}`);
    const lo=date(dates[0]).getTime(),hi=date(dates.at(-1)).getTime();
    const x=d=>L+(date(d).getTime()-lo)/Math.max(1,hi-lo)*(width-L-R);
    const y=v=>T+(100-v)/100*(H-T-B);
    const grid=element('g',{},svg);
    [0,20,40,60,80,100].forEach(v=>{element('line',{x1:L,x2:width-R,y1:y(v),y2:y(v),class:'grid-line'},grid);element('text',{x:L-9,y:y(v)+3,'text-anchor':'end',class:'axis-label'},grid,String(v));});
    element('line',{x1:L,x2:width-R,y1:y(50),y2:y(50),class:'grid-line mid'},grid);
    const ticks=mobile?3:6;
    for(let i=0;i<=ticks;i++){
      const d=new Date(lo+(hi-lo)*i/ticks).toISOString().slice(0,10),v=x(d);
      element('text',{x:v,y:H-7,'text-anchor':i===0?'start':i===ticks?'end':'middle',class:'axis-label'},grid,`${d.slice(2,4)}.${d.slice(5,7)}${period==='3'?'.'+d.slice(8):''}`);
    }
    const lines=element('g',{},svg);
    series.filter(s=>active.has(s.id)).forEach(s=>{
      const list=visible.filter(r=>r.method===s.method);let path='',prev=null;
      list.forEach(r=>{const gap=prev&&(date(r.endDate)-date(prev.endDate)>10*86400000);path+=(prev&&!gap?'L':'M')+x(r.endDate).toFixed(2)+','+y(r[s.key]).toFixed(2)+' ';prev=r;});
      element('path',{d:path,stroke:s.color,'stroke-dasharray':s.method==='ARS'?'6 5':'',class:'series-line','data-series-path':s.id},lines);
      list.forEach(r=>element('circle',{cx:x(r.endDate),cy:y(r[s.key]),r:r.endDate===selected?4.6:mobile?1.5:2.1,fill:s.color,class:'series-dot'},lines));
    });
    const focus=element('g',{},svg),sx=x(selected);
    element('line',{x1:sx,x2:sx,y1:T-4,y2:H-B,class:'focus-line'},focus);
    element('text',{x:Math.min(width-R,Math.max(L,sx)),y:12,'text-anchor':sx>width-70?'end':sx<L+50?'start':'middle',class:'focus-label'},focus,short(selected));
    $('empty-chart').hidden=active.size!==0;
  }
  $('chart').addEventListener('click',e=>{
    const box=$('chart').getBoundingClientRect();const mobile=box.width<560,L=mobile?29:36,R=mobile?10:20;
    const ratio=Math.max(0,Math.min(1,(e.clientX-box.left-L)/(box.width-L-R)));
    const target=date(dates[0]).getTime()+ratio*(date(dates.at(-1))-date(dates[0]));
    let nearest=0;dates.forEach((d,i)=>{if(Math.abs(date(d)-target)<Math.abs(date(dates[nearest])-target))nearest=i;});choose(nearest);
  });
  new ResizeObserver(()=>{if(dates.length)draw();}).observe($('plot'));
  $('audit-summary').textContent=`취임 이후 등록자료 중 전국 정례조사 ${data.regularCount}건을 검토해 국정운영 평가 ${rows.length}건을 수록했습니다. 자료 확인 기준일은 ${fmt(data.collectedAt)}입니다.`;
  const gaps=[];
  ['CATI','ARS'].forEach(m=>{const a=rows.filter(r=>r.method===m);a.forEach((r,i)=>{if(i&&(date(r.endDate)-date(a[i-1].endDate)>10*86400000))gaps.push(`${methodName(m)}: ${fmt(a[i-1].endDate)}–${fmt(r.endDate)}`);});});
  $('audit-details').innerHTML=`<p>검색 기간 ${fmt(data.requestedStart)}–${fmt(data.requestedEnd)}. 조사기관 ‘꽃’ 검색 ${data.listingsCount}건 중 전국 정례조사 ${data.regularCount}건을 검토했습니다. 그 밖의 지역·선거 조사는 대상에서 제외했습니다. 수록 범위는 이 검색 조건에 따른 자료이며 다른 조사기관 자료는 포함하지 않습니다.</p><p>검토 후 제외: ${data.excluded.length}건</p><ul>${data.excluded.map(r=>`<li>${fmt(r.date)} · 등록 ${esc(r.registration)} · ${esc(r.reason)} <a href="${esc(r.sourceUrl)}" target="_blank" rel="noopener noreferrer">원문 ↗</a></li>`).join('')}</ul><p>10일 초과 수록 공백 ${gaps.length}구간. 공백만으로 조사 미실시 여부를 판단하지 않습니다.</p><ul>${gaps.map(g=>`<li>${g}</li>`).join('')}</ul>`;
  updatePeriod();
})();
