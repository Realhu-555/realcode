import{B as K,o as Z,aW as U,d as I,h as r,aH as Y,q as m,aX as Q,aY as F,aZ as V,a_ as H,a$ as E,j as W,b as p,f as P,l as J,u as ee,b0 as re,p as te,s as A,D as x,E as B,F as $,I as j,J as ie,P as G,N as C,K as q,R as L,M as T,L as oe}from"./index-CDIvh3Vh.js";import{a as R,b as ne}from"./ws-CMOh3obd.js";const se=typeof window<"u";let _,N;const ae=()=>{var e,a;_=se?(a=(e=document)===null||e===void 0?void 0:e.fonts)===null||a===void 0?void 0:a.ready:void 0,N=!1,_!==void 0?_.then(()=>{N=!0}):N=!0};ae();function ke(e){if(N)return;let a=!1;K(()=>{N||_==null||_.then(()=>{a||e()})}),Z(()=>{a=!0})}const{c:we}=U(),ze="vueuc-style",le={success:r(E,null),error:r(H,null),warning:r(V,null),info:r(F,null)},ce=I({name:"ProgressCircle",props:{clsPrefix:{type:String,required:!0},status:{type:String,required:!0},strokeWidth:{type:Number,required:!0},fillColor:[String,Object],railColor:String,railStyle:[String,Object],percentage:{type:Number,default:0},offsetDegree:{type:Number,default:0},showIndicator:{type:Boolean,required:!0},indicatorTextColor:String,unit:String,viewBoxWidth:{type:Number,required:!0},gapDegree:{type:Number,required:!0},gapOffsetDegree:{type:Number,default:0}},setup(e,{slots:a}){const d=m(()=>{const o="gradient",{fillColor:i}=e;return typeof i=="object"?`${o}-${Q(JSON.stringify(i))}`:o});function f(o,i,t,n){const{gapDegree:h,viewBoxWidth:l,strokeWidth:v}=e,c=50,y=0,g=c,s=0,S=2*c,k=50+v/2,b=`M ${k},${k} m ${y},${g}
      a ${c},${c} 0 1 1 ${s},${-S}
      a ${c},${c} 0 1 1 ${-s},${S}`,w=Math.PI*2*c,z={stroke:n==="rail"?t:typeof e.fillColor=="object"?`url(#${d.value})`:t,strokeDasharray:`${Math.min(o,100)/100*(w-h)}px ${l*8}px`,strokeDashoffset:`-${h/2}px`,transformOrigin:i?"center":void 0,transform:i?`rotate(${i}deg)`:void 0};return{pathString:b,pathStyle:z}}const u=()=>{const o=typeof e.fillColor=="object",i=o?e.fillColor.stops[0]:"",t=o?e.fillColor.stops[1]:"";return o&&r("defs",null,r("linearGradient",{id:d.value,x1:"0%",y1:"100%",x2:"100%",y2:"0%"},r("stop",{offset:"0%","stop-color":i}),r("stop",{offset:"100%","stop-color":t})))};return()=>{const{fillColor:o,railColor:i,strokeWidth:t,offsetDegree:n,status:h,percentage:l,showIndicator:v,indicatorTextColor:c,unit:y,gapOffsetDegree:g,clsPrefix:s}=e,{pathString:S,pathStyle:k}=f(100,0,i,"rail"),{pathString:b,pathStyle:w}=f(l,n,o,"fill"),z=100+t;return r("div",{class:`${s}-progress-content`,role:"none"},r("div",{class:`${s}-progress-graph`,"aria-hidden":!0},r("div",{class:`${s}-progress-graph-circle`,style:{transform:g?`rotate(${g}deg)`:void 0}},r("svg",{viewBox:`0 0 ${z} ${z}`},u(),r("g",null,r("path",{class:`${s}-progress-graph-circle-rail`,d:S,"stroke-width":t,"stroke-linecap":"round",fill:"none",style:k})),r("g",null,r("path",{class:[`${s}-progress-graph-circle-fill`,l===0&&`${s}-progress-graph-circle-fill--empty`],d:b,"stroke-width":t,"stroke-linecap":"round",fill:"none",style:w}))))),v?r("div",null,a.default?r("div",{class:`${s}-progress-custom-content`,role:"none"},a.default()):h!=="default"?r("div",{class:`${s}-progress-icon`,"aria-hidden":!0},r(Y,{clsPrefix:s},{default:()=>le[h]})):r("div",{class:`${s}-progress-text`,style:{color:c},role:"none"},r("span",{class:`${s}-progress-text__percentage`},l),r("span",{class:`${s}-progress-text__unit`},y))):null)}}}),de={success:r(E,null),error:r(H,null),warning:r(V,null),info:r(F,null)},ue=I({name:"ProgressLine",props:{clsPrefix:{type:String,required:!0},percentage:{type:Number,default:0},railColor:String,railStyle:[String,Object],fillColor:[String,Object],status:{type:String,required:!0},indicatorPlacement:{type:String,required:!0},indicatorTextColor:String,unit:{type:String,default:"%"},processing:{type:Boolean,required:!0},showIndicator:{type:Boolean,required:!0},height:[String,Number],railBorderRadius:[String,Number],fillBorderRadius:[String,Number]},setup(e,{slots:a}){const d=m(()=>R(e.height)),f=m(()=>{var i,t;return typeof e.fillColor=="object"?`linear-gradient(to right, ${(i=e.fillColor)===null||i===void 0?void 0:i.stops[0]} , ${(t=e.fillColor)===null||t===void 0?void 0:t.stops[1]})`:e.fillColor}),u=m(()=>e.railBorderRadius!==void 0?R(e.railBorderRadius):e.height!==void 0?R(e.height,{c:.5}):""),o=m(()=>e.fillBorderRadius!==void 0?R(e.fillBorderRadius):e.railBorderRadius!==void 0?R(e.railBorderRadius):e.height!==void 0?R(e.height,{c:.5}):"");return()=>{const{indicatorPlacement:i,railColor:t,railStyle:n,percentage:h,unit:l,indicatorTextColor:v,status:c,showIndicator:y,processing:g,clsPrefix:s}=e;return r("div",{class:`${s}-progress-content`,role:"none"},r("div",{class:`${s}-progress-graph`,"aria-hidden":!0},r("div",{class:[`${s}-progress-graph-line`,{[`${s}-progress-graph-line--indicator-${i}`]:!0}]},r("div",{class:`${s}-progress-graph-line-rail`,style:[{backgroundColor:t,height:d.value,borderRadius:u.value},n]},r("div",{class:[`${s}-progress-graph-line-fill`,g&&`${s}-progress-graph-line-fill--processing`],style:{maxWidth:`${e.percentage}%`,background:f.value,height:d.value,lineHeight:d.value,borderRadius:o.value}},i==="inside"?r("div",{class:`${s}-progress-graph-line-indicator`,style:{color:v}},a.default?a.default():`${h}${l}`):null)))),y&&i==="outside"?r("div",null,a.default?r("div",{class:`${s}-progress-custom-content`,style:{color:v},role:"none"},a.default()):c==="default"?r("div",{role:"none",class:`${s}-progress-icon ${s}-progress-icon--as-text`,style:{color:v}},h,l):r("div",{class:`${s}-progress-icon`,"aria-hidden":!0},r(Y,{clsPrefix:s},{default:()=>de[c]}))):null)}}});function X(e,a,d=100){return`m ${d/2} ${d/2-e} a ${e} ${e} 0 1 1 0 ${2*e} a ${e} ${e} 0 1 1 0 -${2*e}`}const ge=I({name:"ProgressMultipleCircle",props:{clsPrefix:{type:String,required:!0},viewBoxWidth:{type:Number,required:!0},percentage:{type:Array,default:[0]},strokeWidth:{type:Number,required:!0},circleGap:{type:Number,required:!0},showIndicator:{type:Boolean,required:!0},fillColor:{type:Array,default:()=>[]},railColor:{type:Array,default:()=>[]},railStyle:{type:Array,default:()=>[]}},setup(e,{slots:a}){const d=m(()=>e.percentage.map((o,i)=>`${Math.PI*o/100*(e.viewBoxWidth/2-e.strokeWidth/2*(1+2*i)-e.circleGap*i)*2}, ${e.viewBoxWidth*8}`)),f=(u,o)=>{const i=e.fillColor[o],t=typeof i=="object"?i.stops[0]:"",n=typeof i=="object"?i.stops[1]:"";return typeof e.fillColor[o]=="object"&&r("linearGradient",{id:`gradient-${o}`,x1:"100%",y1:"0%",x2:"0%",y2:"100%"},r("stop",{offset:"0%","stop-color":t}),r("stop",{offset:"100%","stop-color":n}))};return()=>{const{viewBoxWidth:u,strokeWidth:o,circleGap:i,showIndicator:t,fillColor:n,railColor:h,railStyle:l,percentage:v,clsPrefix:c}=e;return r("div",{class:`${c}-progress-content`,role:"none"},r("div",{class:`${c}-progress-graph`,"aria-hidden":!0},r("div",{class:`${c}-progress-graph-circle`},r("svg",{viewBox:`0 0 ${u} ${u}`},r("defs",null,v.map((y,g)=>f(y,g))),v.map((y,g)=>r("g",{key:g},r("path",{class:`${c}-progress-graph-circle-rail`,d:X(u/2-o/2*(1+2*g)-i*g,o,u),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:[{strokeDashoffset:0,stroke:h[g]},l[g]]}),r("path",{class:[`${c}-progress-graph-circle-fill`,y===0&&`${c}-progress-graph-circle-fill--empty`],d:X(u/2-o/2*(1+2*g)-i*g,o,u),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:{strokeDasharray:d.value[g],strokeDashoffset:0,stroke:typeof n[g]=="object"?`url(#gradient-${g})`:n[g]}})))))),t&&a.default?r("div",null,r("div",{class:`${c}-progress-text`},a.default())):null)}}}),pe=W([p("progress",{display:"inline-block"},[p("progress-icon",`
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
 `)]),p("progress-content",{position:"relative"}),p("progress-graph",{position:"relative"},[p("progress-graph-circle",[W("svg",{verticalAlign:"bottom"}),p("progress-graph-circle-fill",`
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
 `,[P("processing",[W("&::after",`
 content: "";
 background-image: var(--n-line-bg-processing);
 animation: progress-processing-animation 2s var(--n-bezier) infinite;
 `)])])])])])]),W("@keyframes progress-processing-animation",`
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
 `)]),fe=Object.assign(Object.assign({},J.props),{processing:Boolean,type:{type:String,default:"line"},gapDegree:Number,gapOffsetDegree:Number,status:{type:String,default:"default"},railColor:[String,Array],railStyle:[String,Array],color:[String,Array,Object],viewBoxWidth:{type:Number,default:100},strokeWidth:{type:Number,default:7},percentage:[Number,Array],unit:{type:String,default:"%"},showIndicator:{type:Boolean,default:!0},indicatorPosition:{type:String,default:"outside"},indicatorPlacement:{type:String,default:"outside"},indicatorTextColor:String,circleGap:{type:Number,default:1},height:Number,borderRadius:[String,Number],fillBorderRadius:[String,Number],offsetDegree:Number}),he=I({name:"Progress",props:fe,setup(e){const a=m(()=>e.indicatorPlacement||e.indicatorPosition),d=m(()=>{if(e.gapDegree||e.gapDegree===0)return e.gapDegree;if(e.type==="dashboard")return 75}),{mergedClsPrefixRef:f,inlineThemeDisabled:u}=ee(e),o=J("Progress","-progress",pe,re,e,f),i=m(()=>{const{status:n}=e,{common:{cubicBezierEaseInOut:h},self:{fontSize:l,fontSizeCircle:v,railColor:c,railHeight:y,iconSizeCircle:g,iconSizeLine:s,textColorCircle:S,textColorLineInner:k,textColorLineOuter:b,lineBgProcessing:w,fontWeightCircle:z,[A("iconColor",n)]:O,[A("fillColor",n)]:D}}=o.value;return{"--n-bezier":h,"--n-fill-color":D,"--n-font-size":l,"--n-font-size-circle":v,"--n-font-weight-circle":z,"--n-icon-color":O,"--n-icon-size-circle":g,"--n-icon-size-line":s,"--n-line-bg-processing":w,"--n-rail-color":c,"--n-rail-height":y,"--n-text-color-circle":S,"--n-text-color-line-inner":k,"--n-text-color-line-outer":b}}),t=u?te("progress",m(()=>e.status[0]),i,e):void 0;return{mergedClsPrefix:f,mergedIndicatorPlacement:a,gapDeg:d,cssVars:u?void 0:i,themeClass:t==null?void 0:t.themeClass,onRender:t==null?void 0:t.onRender}},render(){const{type:e,cssVars:a,indicatorTextColor:d,showIndicator:f,status:u,railColor:o,railStyle:i,color:t,percentage:n,viewBoxWidth:h,strokeWidth:l,mergedIndicatorPlacement:v,unit:c,borderRadius:y,fillBorderRadius:g,height:s,processing:S,circleGap:k,mergedClsPrefix:b,gapDeg:w,gapOffsetDegree:z,themeClass:O,$slots:D,onRender:M}=this;return M==null||M(),r("div",{class:[O,`${b}-progress`,`${b}-progress--${e}`,`${b}-progress--${u}`],style:a,"aria-valuemax":100,"aria-valuemin":0,"aria-valuenow":n,role:e==="circle"||e==="line"||e==="dashboard"?"progressbar":"none"},e==="circle"||e==="dashboard"?r(ce,{clsPrefix:b,status:u,showIndicator:f,indicatorTextColor:d,railColor:o,fillColor:t,railStyle:i,offsetDegree:this.offsetDegree,percentage:n,viewBoxWidth:h,strokeWidth:l,gapDegree:w===void 0?e==="dashboard"?75:0:w,gapOffsetDegree:z,unit:c},D):e==="line"?r(ue,{clsPrefix:b,status:u,showIndicator:f,indicatorTextColor:d,railColor:o,fillColor:t,railStyle:i,percentage:n,processing:S,indicatorPlacement:v,unit:c,fillBorderRadius:g,railBorderRadius:y,height:s},D):e==="multiple-circle"?r(ge,{clsPrefix:b,strokeWidth:l,railColor:o,fillColor:t,railStyle:i,viewBoxWidth:h,percentage:n,showIndicator:f,circleGap:k},D):null)}});function ve(){const e=ne(),a=m(()=>{const t=new Map;for(const n of e.events)t.set(n.agent,n);return t});function d(t){var n;return((n=a.value.get(t))==null?void 0:n.status)==="running"}function f(t){var n;return((n=a.value.get(t))==null?void 0:n.status)==="done"}function u(t){var n;return((n=a.value.get(t))==null?void 0:n.message)??""}const o=m(()=>["gongzhonghao","zhihu","xiaohongshu"].filter(f).length),i=m(()=>["gongzhonghao","zhihu","xiaohongshu"].filter(d).length);return e.connect(),{agentStatuses:a,isRunning:d,isDone:f,getMessage:u,totalDone:o,totalGenerating:i}}const ye={class:"card animate-enter stagger-5"},me={class:"space-y-1"},be={class:"flex-1"},xe={key:2,class:"h-[5px] bg-[var(--border)] rounded-full"},$e={key:0,class:"mt-4 pt-4 border-t border-[var(--border)] text-xs text-center text-muted"},Pe=I({__name:"ProgressTimeline",setup(e){const{isRunning:a,isDone:d,totalDone:f,totalGenerating:u}=ve(),o=[{id:"celve",label:"策略分析",icon:"🧠"},{id:"gongzhonghao",label:"公众号",icon:"📰"},{id:"zhihu",label:"知乎",icon:"💡"},{id:"xiaohongshu",label:"小红书",icon:"✨"},{id:"shenjiao",label:"审校",icon:"🔍"}];function i(t){return d(t)?"text-[var(--success)]":a(t)?"text-[var(--accent)]":"text-muted"}return(t,n)=>{const h=he;return x(),B("div",ye,[n[0]||(n[0]=$("div",{class:"flex items-center gap-3 mb-5"},[$("div",{class:"accent-line"}),$("h3",{class:"heading-section"},"生成进度")],-1)),$("div",me,[(x(),B(j,null,ie(o,l=>$("div",{key:l.id,class:"flex items-center gap-3 py-2 px-2 -mx-2 rounded-lg transition-colors hover:bg-[var(--bg-hover)]"},[$("span",{class:G(["text-lg w-8 text-center shrink-0",{"opacity-40":!C(d)(l.id)&&!C(a)(l.id)}])},q(l.icon),3),$("span",{class:G(["text-sm w-20 shrink-0",i(l.id)])},q(l.label),3),$("div",be,[C(a)(l.id)?(x(),L(h,{key:0,type:"line",percentage:50,height:5,"indicator-placement":"none",processing:""})):C(d)(l.id)?(x(),L(h,{key:1,type:"line",percentage:100,height:5,"indicator-placement":"none",color:"var(--success)"})):(x(),B("div",xe))]),$("span",{class:G(["text-xs w-14 text-right shrink-0",i(l.id)])},[C(d)(l.id)?(x(),B(j,{key:0},[T("✓ 完成")],64)):C(a)(l.id)?(x(),B(j,{key:1},[T("⏳ 中")],64)):(x(),B(j,{key:2},[T("等待")],64))],2)])),64))]),C(u)>0?(x(),B("div",$e," 并行生成 "+q(C(u))+" 篇内容  ·  已完成 "+q(C(f))+"/3 ",1)):oe("",!0)])}}});export{Pe as _,we as a,ze as c,ke as o};
