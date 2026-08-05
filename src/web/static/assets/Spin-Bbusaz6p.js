import{w,x as d,Q as V,L as g,aR as x,aS as j,m as y,j as u,av as k,l as h,f as R,h as o,a8 as _,T as O,u as P,p as S,v as A,aD as B,r as E,aT as W,aU as L,aV as I,y as D}from"./index-Ch5gdr_H.js";function Y(e,n){return w(e,t=>{t!==void 0&&(n.value=t)}),d(()=>e.value===void 0?n.value:e.value)}function H(e,n){return d(()=>{for(const t of n)if(e[t]!==void 0)return e[t];return e[n[n.length-1]]})}const K=/^(\d|\.)+$/,v=/(\d|\.)+/;function q(e,{c:n=1,offset:t=0,attachPx:s=!0}={}){if(typeof e=="number"){const i=(e+t)*n;return i===0?"0":`${i}px`}else if(typeof e=="string")if(K.test(e)){const i=(Number(e)+t)*n;return s?i===0?"0":`${i}px`:`${i}`}else{const i=v.exec(e);return i?e.replace(v,String((Number(i[0])+t)*n)):e}return e}function M(e,...n){if(Array.isArray(e))e.forEach(t=>M(t,...n));else return e(...n)}function b(e,n=!0,t=[]){return e.forEach(s=>{if(s!==null){if(typeof s!="object"){(typeof s=="string"||typeof s=="number")&&t.push(V(String(s)));return}if(Array.isArray(s)){b(s,n,t);return}if(s.type===g){if(s.children===null)return;Array.isArray(s.children)&&b(s.children,n,t)}else{if(s.type===x&&n)return;t.push(s)}}}),t}function m(e){return e.some(n=>j(n)?!(n.type===x||n.type===g&&!m(n.children)):!0)?e:null}function G(e,n){return e&&m(e())||n()}function J(e,n,t){return e&&m(e(n))||t(n)}function Z(e,n){const t=e&&m(e());return n(t||null)}function N(e){return!(e&&m(e()))}const F=y([y("@keyframes spin-rotate",`
 from {
 transform: rotate(0);
 }
 to {
 transform: rotate(360deg);
 }
 `),u("spin-container",`
 position: relative;
 `,[u("spin-body",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[k()])]),u("spin-body",`
 display: inline-flex;
 align-items: center;
 justify-content: center;
 flex-direction: column;
 `),u("spin",`
 display: inline-flex;
 height: var(--n-size);
 width: var(--n-size);
 font-size: var(--n-size);
 color: var(--n-color);
 `,[h("rotate",`
 animation: spin-rotate 2s linear infinite;
 `)]),u("spin-description",`
 display: inline-block;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 margin-top: 8px;
 `),u("spin-content",`
 opacity: 1;
 transition: opacity .3s var(--n-bezier);
 pointer-events: all;
 `,[h("spinning",`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),Q={small:20,medium:18,large:16},U=Object.assign(Object.assign(Object.assign({},S.props),{contentClass:String,contentStyle:[Object,String],description:String,size:{type:[String,Number],default:"medium"},show:{type:Boolean,default:!0},rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number}),W),ee=R({name:"Spin",props:U,slots:Object,setup(e){const{mergedClsPrefixRef:n,inlineThemeDisabled:t}=P(e),s=S("Spin","-spin",F,L,e,n),i=d(()=>{const{size:r}=e,{common:{cubicBezierEaseInOut:c},self:p}=s.value,{opacitySpinning:z,color:C,textColor:$}=p,T=typeof r=="number"?I(r):p[D("size",r)];return{"--n-bezier":c,"--n-opacity-spinning":z,"--n-size":T,"--n-color":C,"--n-text-color":$}}),a=t?A("spin",d(()=>{const{size:r}=e;return typeof r=="number"?String(r):r[0]}),i,e):void 0,f=H(e,["spinning","show"]),l=E(!1);return B(r=>{let c;if(f.value){const{delay:p}=e;if(p){c=window.setTimeout(()=>{l.value=!0},p),r(()=>{clearTimeout(c)});return}}l.value=f.value}),{mergedClsPrefix:n,active:l,mergedStrokeWidth:d(()=>{const{strokeWidth:r}=e;if(r!==void 0)return r;const{size:c}=e;return Q[typeof c=="number"?"medium":c]}),cssVars:t?void 0:i,themeClass:a==null?void 0:a.themeClass,onRender:a==null?void 0:a.onRender}},render(){var e,n;const{$slots:t,mergedClsPrefix:s,description:i}=this,a=t.icon&&this.rotate,f=(i||t.description)&&o("div",{class:`${s}-spin-description`},i||((e=t.description)===null||e===void 0?void 0:e.call(t))),l=t.icon?o("div",{class:[`${s}-spin-body`,this.themeClass]},o("div",{class:[`${s}-spin`,a&&`${s}-spin--rotate`],style:t.default?"":this.cssVars},t.icon()),f):o("div",{class:[`${s}-spin-body`,this.themeClass]},o(_,{clsPrefix:s,style:t.default?"":this.cssVars,stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,radius:this.radius,scale:this.scale,class:`${s}-spin`}),f);return(n=this.onRender)===null||n===void 0||n.call(this),t.default?o("div",{class:[`${s}-spin-container`,this.themeClass],style:this.cssVars},o("div",{class:[`${s}-spin-content`,this.active&&`${s}-spin-content--spinning`,this.contentClass],style:this.contentStyle},t),o(O,{name:"fade-in-transition"},{default:()=>this.active?l:null})):l}});export{ee as _,q as a,G as b,M as c,J as d,m as e,b as f,H as g,N as i,Z as r,Y as u};
