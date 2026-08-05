import{g as F,f as N,h as r,aj as L,x as v,aP as Q,ao as X,am as V,al as Y,an as H,m as _,j as p,l as P,p as E,u as J,aQ as K,v as U,y as T,U as Z,G as x,H as B,I as $,L as I,N as ee,V as q,R as C,O as W,X as M,Q as G,P as re}from"./index-Ch5gdr_H.js";import{a as R}from"./Spin-Bbusaz6p.js";function ve(){return F()!==null}const be=typeof window<"u",te={success:r(H,null),error:r(Y,null),warning:r(V,null),info:r(X,null)},ie=N({name:"ProgressCircle",props:{clsPrefix:{type:String,required:!0},status:{type:String,required:!0},strokeWidth:{type:Number,required:!0},fillColor:[String,Object],railColor:String,railStyle:[String,Object],percentage:{type:Number,default:0},offsetDegree:{type:Number,default:0},showIndicator:{type:Boolean,required:!0},indicatorTextColor:String,unit:String,viewBoxWidth:{type:Number,required:!0},gapDegree:{type:Number,required:!0},gapOffsetDegree:{type:Number,default:0}},setup(e,{slots:l}){const d=v(()=>{const o="gradient",{fillColor:i}=e;return typeof i=="object"?`${o}-${Q(JSON.stringify(i))}`:o});function f(o,i,t,n){const{gapDegree:h,viewBoxWidth:a,strokeWidth:m}=e,c=50,y=0,u=c,s=0,S=2*c,k=50+m/2,b=`M ${k},${k} m ${y},${u}
      a ${c},${c} 0 1 1 ${s},${-S}
      a ${c},${c} 0 1 1 ${-s},${S}`,w=Math.PI*2*c,z={stroke:n==="rail"?t:typeof e.fillColor=="object"?`url(#${d.value})`:t,strokeDasharray:`${Math.min(o,100)/100*(w-h)}px ${a*8}px`,strokeDashoffset:`-${h/2}px`,transformOrigin:i?"center":void 0,transform:i?`rotate(${i}deg)`:void 0};return{pathString:b,pathStyle:z}}const g=()=>{const o=typeof e.fillColor=="object",i=o?e.fillColor.stops[0]:"",t=o?e.fillColor.stops[1]:"";return o&&r("defs",null,r("linearGradient",{id:d.value,x1:"0%",y1:"100%",x2:"100%",y2:"0%"},r("stop",{offset:"0%","stop-color":i}),r("stop",{offset:"100%","stop-color":t})))};return()=>{const{fillColor:o,railColor:i,strokeWidth:t,offsetDegree:n,status:h,percentage:a,showIndicator:m,indicatorTextColor:c,unit:y,gapOffsetDegree:u,clsPrefix:s}=e,{pathString:S,pathStyle:k}=f(100,0,i,"rail"),{pathString:b,pathStyle:w}=f(a,n,o,"fill"),z=100+t;return r("div",{class:`${s}-progress-content`,role:"none"},r("div",{class:`${s}-progress-graph`,"aria-hidden":!0},r("div",{class:`${s}-progress-graph-circle`,style:{transform:u?`rotate(${u}deg)`:void 0}},r("svg",{viewBox:`0 0 ${z} ${z}`},g(),r("g",null,r("path",{class:`${s}-progress-graph-circle-rail`,d:S,"stroke-width":t,"stroke-linecap":"round",fill:"none",style:k})),r("g",null,r("path",{class:[`${s}-progress-graph-circle-fill`,a===0&&`${s}-progress-graph-circle-fill--empty`],d:b,"stroke-width":t,"stroke-linecap":"round",fill:"none",style:w}))))),m?r("div",null,l.default?r("div",{class:`${s}-progress-custom-content`,role:"none"},l.default()):h!=="default"?r("div",{class:`${s}-progress-icon`,"aria-hidden":!0},r(L,{clsPrefix:s},{default:()=>te[h]})):r("div",{class:`${s}-progress-text`,style:{color:c},role:"none"},r("span",{class:`${s}-progress-text__percentage`},a),r("span",{class:`${s}-progress-text__unit`},y))):null)}}}),oe={success:r(H,null),error:r(Y,null),warning:r(V,null),info:r(X,null)},ne=N({name:"ProgressLine",props:{clsPrefix:{type:String,required:!0},percentage:{type:Number,default:0},railColor:String,railStyle:[String,Object],fillColor:[String,Object],status:{type:String,required:!0},indicatorPlacement:{type:String,required:!0},indicatorTextColor:String,unit:{type:String,default:"%"},processing:{type:Boolean,required:!0},showIndicator:{type:Boolean,required:!0},height:[String,Number],railBorderRadius:[String,Number],fillBorderRadius:[String,Number]},setup(e,{slots:l}){const d=v(()=>R(e.height)),f=v(()=>{var i,t;return typeof e.fillColor=="object"?`linear-gradient(to right, ${(i=e.fillColor)===null||i===void 0?void 0:i.stops[0]} , ${(t=e.fillColor)===null||t===void 0?void 0:t.stops[1]})`:e.fillColor}),g=v(()=>e.railBorderRadius!==void 0?R(e.railBorderRadius):e.height!==void 0?R(e.height,{c:.5}):""),o=v(()=>e.fillBorderRadius!==void 0?R(e.fillBorderRadius):e.railBorderRadius!==void 0?R(e.railBorderRadius):e.height!==void 0?R(e.height,{c:.5}):"");return()=>{const{indicatorPlacement:i,railColor:t,railStyle:n,percentage:h,unit:a,indicatorTextColor:m,status:c,showIndicator:y,processing:u,clsPrefix:s}=e;return r("div",{class:`${s}-progress-content`,role:"none"},r("div",{class:`${s}-progress-graph`,"aria-hidden":!0},r("div",{class:[`${s}-progress-graph-line`,{[`${s}-progress-graph-line--indicator-${i}`]:!0}]},r("div",{class:`${s}-progress-graph-line-rail`,style:[{backgroundColor:t,height:d.value,borderRadius:g.value},n]},r("div",{class:[`${s}-progress-graph-line-fill`,u&&`${s}-progress-graph-line-fill--processing`],style:{maxWidth:`${e.percentage}%`,background:f.value,height:d.value,lineHeight:d.value,borderRadius:o.value}},i==="inside"?r("div",{class:`${s}-progress-graph-line-indicator`,style:{color:m}},l.default?l.default():`${h}${a}`):null)))),y&&i==="outside"?r("div",null,l.default?r("div",{class:`${s}-progress-custom-content`,style:{color:m},role:"none"},l.default()):c==="default"?r("div",{role:"none",class:`${s}-progress-icon ${s}-progress-icon--as-text`,style:{color:m}},h,a):r("div",{class:`${s}-progress-icon`,"aria-hidden":!0},r(L,{clsPrefix:s},{default:()=>oe[c]}))):null)}}});function A(e,l,d=100){return`m ${d/2} ${d/2-e} a ${e} ${e} 0 1 1 0 ${2*e} a ${e} ${e} 0 1 1 0 -${2*e}`}const se=N({name:"ProgressMultipleCircle",props:{clsPrefix:{type:String,required:!0},viewBoxWidth:{type:Number,required:!0},percentage:{type:Array,default:[0]},strokeWidth:{type:Number,required:!0},circleGap:{type:Number,required:!0},showIndicator:{type:Boolean,required:!0},fillColor:{type:Array,default:()=>[]},railColor:{type:Array,default:()=>[]},railStyle:{type:Array,default:()=>[]}},setup(e,{slots:l}){const d=v(()=>e.percentage.map((o,i)=>`${Math.PI*o/100*(e.viewBoxWidth/2-e.strokeWidth/2*(1+2*i)-e.circleGap*i)*2}, ${e.viewBoxWidth*8}`)),f=(g,o)=>{const i=e.fillColor[o],t=typeof i=="object"?i.stops[0]:"",n=typeof i=="object"?i.stops[1]:"";return typeof e.fillColor[o]=="object"&&r("linearGradient",{id:`gradient-${o}`,x1:"100%",y1:"0%",x2:"0%",y2:"100%"},r("stop",{offset:"0%","stop-color":t}),r("stop",{offset:"100%","stop-color":n}))};return()=>{const{viewBoxWidth:g,strokeWidth:o,circleGap:i,showIndicator:t,fillColor:n,railColor:h,railStyle:a,percentage:m,clsPrefix:c}=e;return r("div",{class:`${c}-progress-content`,role:"none"},r("div",{class:`${c}-progress-graph`,"aria-hidden":!0},r("div",{class:`${c}-progress-graph-circle`},r("svg",{viewBox:`0 0 ${g} ${g}`},r("defs",null,m.map((y,u)=>f(y,u))),m.map((y,u)=>r("g",{key:u},r("path",{class:`${c}-progress-graph-circle-rail`,d:A(g/2-o/2*(1+2*u)-i*u,o,g),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:[{strokeDashoffset:0,stroke:h[u]},a[u]]}),r("path",{class:[`${c}-progress-graph-circle-fill`,y===0&&`${c}-progress-graph-circle-fill--empty`],d:A(g/2-o/2*(1+2*u)-i*u,o,g),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:{strokeDasharray:d.value[u],strokeDashoffset:0,stroke:typeof n[u]=="object"?`url(#gradient-${u})`:n[u]}})))))),t&&l.default?r("div",null,r("div",{class:`${c}-progress-text`},l.default())):null)}}}),ae=_([p("progress",{display:"inline-block"},[p("progress-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 `),P("line",`
 width: 100%;
 display: block;
 `,[p("progress-content",`
 display: flex;
 align-items: center;
 `,[p("progress-graph",{flex:1})]),p("progress-custom-content",{marginLeft:"14px"}),p("progress-icon",`
 width: 30px;
 padding-left: 14px;
 height: var(--n-icon-size-line);
 line-height: var(--n-icon-size-line);
 font-size: var(--n-icon-size-line);
 `,[P("as-text",`
 color: var(--n-text-color-line-outer);
 text-align: center;
 width: 40px;
 font-size: var(--n-font-size);
 padding-left: 4px;
 transition: color .3s var(--n-bezier);
 `)])]),P("circle, dashboard",{width:"120px"},[p("progress-custom-content",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 justify-content: center;
 `),p("progress-text",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 color: inherit;
 font-size: var(--n-font-size-circle);
 color: var(--n-text-color-circle);
 font-weight: var(--n-font-weight-circle);
 transition: color .3s var(--n-bezier);
 white-space: nowrap;
 `),p("progress-icon",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 color: var(--n-icon-color);
 font-size: var(--n-icon-size-circle);
 `)]),P("multiple-circle",`
 width: 200px;
 color: inherit;
 `,[p("progress-text",`
 font-weight: var(--n-font-weight-circle);
 color: var(--n-text-color-circle);
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 justify-content: center;
 transition: color .3s var(--n-bezier);
 `)]),p("progress-content",{position:"relative"}),p("progress-graph",{position:"relative"},[p("progress-graph-circle",[_("svg",{verticalAlign:"bottom"}),p("progress-graph-circle-fill",`
 stroke: var(--n-fill-color);
 transition:
 opacity .3s var(--n-bezier),
 stroke .3s var(--n-bezier),
 stroke-dasharray .3s var(--n-bezier);
 `,[P("empty",{opacity:0})]),p("progress-graph-circle-rail",`
 transition: stroke .3s var(--n-bezier);
 overflow: hidden;
 stroke: var(--n-rail-color);
 `)]),p("progress-graph-line",[P("indicator-inside",[p("progress-graph-line-rail",`
 height: 16px;
 line-height: 16px;
 border-radius: 10px;
 `,[p("progress-graph-line-fill",`
 height: inherit;
 border-radius: 10px;
 `),p("progress-graph-line-indicator",`
 background: #0000;
 white-space: nowrap;
 text-align: right;
 margin-left: 14px;
 margin-right: 14px;
 height: inherit;
 font-size: 12px;
 color: var(--n-text-color-line-inner);
 transition: color .3s var(--n-bezier);
 `)])]),P("indicator-inside-label",`
 height: 16px;
 display: flex;
 align-items: center;
 `,[p("progress-graph-line-rail",`
 flex: 1;
 transition: background-color .3s var(--n-bezier);
 `),p("progress-graph-line-indicator",`
 background: var(--n-fill-color);
 font-size: 12px;
 transform: translateZ(0);
 display: flex;
 vertical-align: middle;
 height: 16px;
 line-height: 16px;
 padding: 0 10px;
 border-radius: 10px;
 position: absolute;
 white-space: nowrap;
 color: var(--n-text-color-line-inner);
 transition:
 right .2s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `)]),p("progress-graph-line-rail",`
 position: relative;
 overflow: hidden;
 height: var(--n-rail-height);
 border-radius: 5px;
 background-color: var(--n-rail-color);
 transition: background-color .3s var(--n-bezier);
 `,[p("progress-graph-line-fill",`
 background: var(--n-fill-color);
 position: relative;
 border-radius: 5px;
 height: inherit;
 width: 100%;
 max-width: 0%;
 transition:
 background-color .3s var(--n-bezier),
 max-width .2s var(--n-bezier);
 `,[P("processing",[_("&::after",`
 content: "";
 background-image: var(--n-line-bg-processing);
 animation: progress-processing-animation 2s var(--n-bezier) infinite;
 `)])])])])])]),_("@keyframes progress-processing-animation",`
 0% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 100%;
 opacity: 1;
 }
 66% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 0;
 }
 100% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 0;
 }
 `)]),le=Object.assign(Object.assign({},E.props),{processing:Boolean,type:{type:String,default:"line"},gapDegree:Number,gapOffsetDegree:Number,status:{type:String,default:"default"},railColor:[String,Array],railStyle:[String,Array],color:[String,Array,Object],viewBoxWidth:{type:Number,default:100},strokeWidth:{type:Number,default:7},percentage:[Number,Array],unit:{type:String,default:"%"},showIndicator:{type:Boolean,default:!0},indicatorPosition:{type:String,default:"outside"},indicatorPlacement:{type:String,default:"outside"},indicatorTextColor:String,circleGap:{type:Number,default:1},height:Number,borderRadius:[String,Number],fillBorderRadius:[String,Number],offsetDegree:Number}),ce=N({name:"Progress",props:le,setup(e){const l=v(()=>e.indicatorPlacement||e.indicatorPosition),d=v(()=>{if(e.gapDegree||e.gapDegree===0)return e.gapDegree;if(e.type==="dashboard")return 75}),{mergedClsPrefixRef:f,inlineThemeDisabled:g}=J(e),o=E("Progress","-progress",ae,K,e,f),i=v(()=>{const{status:n}=e,{common:{cubicBezierEaseInOut:h},self:{fontSize:a,fontSizeCircle:m,railColor:c,railHeight:y,iconSizeCircle:u,iconSizeLine:s,textColorCircle:S,textColorLineInner:k,textColorLineOuter:b,lineBgProcessing:w,fontWeightCircle:z,[T("iconColor",n)]:j,[T("fillColor",n)]:D}}=o.value;return{"--n-bezier":h,"--n-fill-color":D,"--n-font-size":a,"--n-font-size-circle":m,"--n-font-weight-circle":z,"--n-icon-color":j,"--n-icon-size-circle":u,"--n-icon-size-line":s,"--n-line-bg-processing":w,"--n-rail-color":c,"--n-rail-height":y,"--n-text-color-circle":S,"--n-text-color-line-inner":k,"--n-text-color-line-outer":b}}),t=g?U("progress",v(()=>e.status[0]),i,e):void 0;return{mergedClsPrefix:f,mergedIndicatorPlacement:l,gapDeg:d,cssVars:g?void 0:i,themeClass:t==null?void 0:t.themeClass,onRender:t==null?void 0:t.onRender}},render(){const{type:e,cssVars:l,indicatorTextColor:d,showIndicator:f,status:g,railColor:o,railStyle:i,color:t,percentage:n,viewBoxWidth:h,strokeWidth:a,mergedIndicatorPlacement:m,unit:c,borderRadius:y,fillBorderRadius:u,height:s,processing:S,circleGap:k,mergedClsPrefix:b,gapDeg:w,gapOffsetDegree:z,themeClass:j,$slots:D,onRender:O}=this;return O==null||O(),r("div",{class:[j,`${b}-progress`,`${b}-progress--${e}`,`${b}-progress--${g}`],style:l,"aria-valuemax":100,"aria-valuemin":0,"aria-valuenow":n,role:e==="circle"||e==="line"||e==="dashboard"?"progressbar":"none"},e==="circle"||e==="dashboard"?r(ie,{clsPrefix:b,status:g,showIndicator:f,indicatorTextColor:d,railColor:o,fillColor:t,railStyle:i,offsetDegree:this.offsetDegree,percentage:n,viewBoxWidth:h,strokeWidth:a,gapDegree:w===void 0?e==="dashboard"?75:0:w,gapOffsetDegree:z,unit:c},D):e==="line"?r(ne,{clsPrefix:b,status:g,showIndicator:f,indicatorTextColor:d,railColor:o,fillColor:t,railStyle:i,percentage:n,processing:S,indicatorPlacement:m,unit:c,fillBorderRadius:u,railBorderRadius:y,height:s},D):e==="multiple-circle"?r(se,{clsPrefix:b,strokeWidth:a,railColor:o,fillColor:t,railStyle:i,viewBoxWidth:h,percentage:n,showIndicator:f,circleGap:k},D):null)}});function de(){const e=Z(),l=v(()=>{const t=new Map;for(const n of e.events)t.set(n.agent,n);return t});function d(t){var n;return((n=l.value.get(t))==null?void 0:n.status)==="running"}function f(t){var n;return((n=l.value.get(t))==null?void 0:n.status)==="done"}function g(t){var n;return((n=l.value.get(t))==null?void 0:n.message)??""}const o=v(()=>["gongzhonghao","zhihu","xiaohongshu"].filter(f).length),i=v(()=>["gongzhonghao","zhihu","xiaohongshu"].filter(d).length);return e.connect(),{agentStatuses:l,isRunning:d,isDone:f,getMessage:g,totalDone:o,totalGenerating:i}}const ge={class:"card animate-enter stagger-5"},ue={class:"space-y-1"},pe={class:"flex-1"},fe={key:2,class:"h-[5px] bg-[var(--border)] rounded-full"},he={key:0,class:"mt-4 pt-4 border-t border-[var(--border)] text-xs text-center text-muted"},xe=N({__name:"ProgressTimeline",setup(e){const{isRunning:l,isDone:d,totalDone:f,totalGenerating:g}=de(),o=[{id:"celve",label:"策略分析",icon:"🧠"},{id:"gongzhonghao",label:"公众号",icon:"📰"},{id:"zhihu",label:"知乎",icon:"💡"},{id:"xiaohongshu",label:"小红书",icon:"✨"},{id:"shenjiao",label:"审校",icon:"🔍"}];function i(t){return d(t)?"text-[var(--success)]":l(t)?"text-[var(--accent)]":"text-muted"}return(t,n)=>{const h=ce;return x(),B("div",ge,[n[0]||(n[0]=$("div",{class:"flex items-center gap-3 mb-5"},[$("div",{class:"accent-line"}),$("h3",{class:"heading-section"},"生成进度")],-1)),$("div",ue,[(x(),B(I,null,ee(o,a=>$("div",{key:a.id,class:"flex items-center gap-3 py-2 px-2 -mx-2 rounded-lg transition-colors hover:bg-[var(--bg-hover)]"},[$("span",{class:q(["text-lg w-8 text-center shrink-0",{"opacity-40":!C(d)(a.id)&&!C(l)(a.id)}])},W(a.icon),3),$("span",{class:q(["text-sm w-20 shrink-0",i(a.id)])},W(a.label),3),$("div",pe,[C(l)(a.id)?(x(),M(h,{key:0,type:"line",percentage:50,height:5,"indicator-placement":"none",processing:""})):C(d)(a.id)?(x(),M(h,{key:1,type:"line",percentage:100,height:5,"indicator-placement":"none",color:"var(--success)"})):(x(),B("div",fe))]),$("span",{class:q(["text-xs w-14 text-right shrink-0",i(a.id)])},[C(d)(a.id)?(x(),B(I,{key:0},[G("✓ 完成")],64)):C(l)(a.id)?(x(),B(I,{key:1},[G("⏳ 中")],64)):(x(),B(I,{key:2},[G("等待")],64))],2)])),64))]),C(g)>0?(x(),B("div",he," 并行生成 "+W(C(g))+" 篇内容  ·  已完成 "+W(C(f))+"/3 ",1)):re("",!0)])}}});export{xe as _,ve as h,be as i};
