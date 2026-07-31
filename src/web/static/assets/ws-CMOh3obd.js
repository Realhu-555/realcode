import{w as k,q as p,M as V,I as S,W as x,b1 as W,j as h,b as f,b2 as _,f as b,d as j,h as c,aJ as O,T as E,u as P,l as z,p as R,ar as A,r as y,b3 as B,b4 as I,b5 as L,s as M,b6 as D,b7 as H}from"./index-CDIvh3Vh.js";function G(e,n){return k(e,t=>{t!==void 0&&(n.value=t)}),p(()=>e.value===void 0?n.value:e.value)}function J(e,n){return p(()=>{for(const t of n)if(e[t]!==void 0)return e[t];return e[n[n.length-1]]})}const K=/^(\d|\.)+$/,v=/(\d|\.)+/;function Q(e,{c:n=1,offset:t=0,attachPx:s=!0}={}){if(typeof e=="number"){const i=(e+t)*n;return i===0?"0":`${i}px`}else if(typeof e=="string")if(K.test(e)){const i=(Number(e)+t)*n;return s?i===0?"0":`${i}px`:`${i}`}else{const i=v.exec(e);return i?e.replace(v,String((Number(i[0])+t)*n)):e}return e}function q(e,...n){if(Array.isArray(e))e.forEach(t=>q(t,...n));else return e(...n)}function g(e,n=!0,t=[]){return e.forEach(s=>{if(s!==null){if(typeof s!="object"){(typeof s=="string"||typeof s=="number")&&t.push(V(String(s)));return}if(Array.isArray(s)){g(s,n,t);return}if(s.type===S){if(s.children===null)return;Array.isArray(s.children)&&g(s.children,n,t)}else{if(s.type===x&&n)return;t.push(s)}}}),t}function m(e){return e.some(n=>W(n)?!(n.type===x||n.type===S&&!m(n.children)):!0)?e:null}function Z(e,n){return e&&m(e())||n()}function N(e,n,t){return e&&m(e(n))||t(n)}function ee(e,n){const t=e&&m(e());return n(t||null)}function ne(e){return!(e&&m(e()))}const F=h([h("@keyframes spin-rotate",`
 from {
 transform: rotate(0);
 }
 to {
 transform: rotate(360deg);
 }
 `),f("spin-container",`
 position: relative;
 `,[f("spin-body",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[_()])]),f("spin-body",`
 display: inline-flex;
 align-items: center;
 justify-content: center;
 flex-direction: column;
 `),f("spin",`
 display: inline-flex;
 height: var(--n-size);
 width: var(--n-size);
 font-size: var(--n-size);
 color: var(--n-color);
 `,[b("rotate",`
 animation: spin-rotate 2s linear infinite;
 `)]),f("spin-description",`
 display: inline-block;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 margin-top: 8px;
 `),f("spin-content",`
 opacity: 1;
 transition: opacity .3s var(--n-bezier);
 pointer-events: all;
 `,[b("spinning",`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),U={small:20,medium:18,large:16},X=Object.assign(Object.assign(Object.assign({},z.props),{contentClass:String,contentStyle:[Object,String],description:String,size:{type:[String,Number],default:"medium"},show:{type:Boolean,default:!0},rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number}),B),te=j({name:"Spin",props:X,slots:Object,setup(e){const{mergedClsPrefixRef:n,inlineThemeDisabled:t}=P(e),s=z("Spin","-spin",F,I,e,n),i=p(()=>{const{size:r}=e,{common:{cubicBezierEaseInOut:o},self:d}=s.value,{opacitySpinning:w,color:C,textColor:$}=d,T=typeof r=="number"?L(r):d[M("size",r)];return{"--n-bezier":o,"--n-opacity-spinning":w,"--n-size":T,"--n-color":C,"--n-text-color":$}}),a=t?R("spin",p(()=>{const{size:r}=e;return typeof r=="number"?String(r):r[0]}),i,e):void 0,l=J(e,["spinning","show"]),u=y(!1);return A(r=>{let o;if(l.value){const{delay:d}=e;if(d){o=window.setTimeout(()=>{u.value=!0},d),r(()=>{clearTimeout(o)});return}}u.value=l.value}),{mergedClsPrefix:n,active:u,mergedStrokeWidth:p(()=>{const{strokeWidth:r}=e;if(r!==void 0)return r;const{size:o}=e;return U[typeof o=="number"?"medium":o]}),cssVars:t?void 0:i,themeClass:a==null?void 0:a.themeClass,onRender:a==null?void 0:a.onRender}},render(){var e,n;const{$slots:t,mergedClsPrefix:s,description:i}=this,a=t.icon&&this.rotate,l=(i||t.description)&&c("div",{class:`${s}-spin-description`},i||((e=t.description)===null||e===void 0?void 0:e.call(t))),u=t.icon?c("div",{class:[`${s}-spin-body`,this.themeClass]},c("div",{class:[`${s}-spin`,a&&`${s}-spin--rotate`],style:t.default?"":this.cssVars},t.icon()),l):c("div",{class:[`${s}-spin-body`,this.themeClass]},c(O,{clsPrefix:s,style:t.default?"":this.cssVars,stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,radius:this.radius,scale:this.scale,class:`${s}-spin`}),l);return(n=this.onRender)===null||n===void 0||n.call(this),t.default?c("div",{class:[`${s}-spin-container`,this.themeClass],style:this.cssVars},c("div",{class:[`${s}-spin-content`,this.active&&`${s}-spin-content--spinning`,this.contentClass],style:this.contentStyle},t),c(E,{name:"fade-in-transition"},{default:()=>this.active?u:null})):u}}),se=D("ws",()=>{const e=y(!1),n=y([]),t=`ws://${window.location.host}/ws`;let s=null;function i(){s||(s=H(t,{immediate:!0,onConnected(){e.value=!0},onDisconnected(){e.value=!1},onMessage(u,r){try{const o=JSON.parse(r.data);n.value.push(o),n.value.length>100&&(n.value=n.value.slice(-100))}catch{}}}))}function a(){s==null||s.close(),s=null,e.value=!1}function l(){n.value=[]}return{connected:e,events:n,connect:i,disconnect:a,clearEvents:l}});export{te as _,Q as a,se as b,q as c,J as d,Z as e,g as f,N as g,ne as i,ee as r,G as u};
