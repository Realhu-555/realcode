import{E as we,o as Pt,aF as Wt,f as U,h as f,r as P,aG as Bt,b as Lt,aH as le,aI as Et,d as jt,i as He,aJ as At,ar as It,L as Me,aj as Ot,ai as Ht,af as Mt,x as V,aK as Ft,j as r,l,m as S,k as T,n as Dt,aC as ue,u as Nt,p as Fe,w as pe,aD as Vt,v as Ut,aL as Xt,as as Gt,aM as Kt,aq as Yt,aN as qt,a3 as ve,y as H,ah as se,at as Jt,z as Qt,e as M,aO as Zt,G as E,H as I,V as De,I as m,O as K,R as N,P as ea,J as te,K as de,S as ta,U as aa,ay as na,N as ra,X as Pe}from"./index-Ch5gdr_H.js";import{f as he,r as We,u as oa,g as Be,c as ie,_ as Ne}from"./Spin-Bbusaz6p.js";import{i as sa,_ as ia}from"./ProgressTimeline.vue_vue_type_script_setup_true_lang-DoVE8O_p.js";let Z,ae;const la=()=>{var e,n;Z=sa?(n=(e=document)===null||e===void 0?void 0:e.fonts)===null||n===void 0?void 0:n.ready:void 0,ae=!1,Z!==void 0?Z.then(()=>{ae=!0}):ae=!0};la();function da(e){if(ae)return;let n=!1;we(()=>{ae||Z==null||Z.then(()=>{n||e()})}),Pt(()=>{n=!0})}const{c:Le}=Wt(),ca="vueuc-style",ba=Le(".v-x-scroll",{overflow:"auto",scrollbarWidth:"none"},[Le("&::-webkit-scrollbar",{width:0,height:0})]),fa=U({name:"XScroll",props:{disabled:Boolean,onScroll:Function},setup(){const e=P(null);function n(i){!(i.currentTarget.offsetWidth<i.currentTarget.scrollWidth)||i.deltaY===0||(i.currentTarget.scrollLeft+=i.deltaY+i.deltaX,i.preventDefault())}const o=Bt();return ba.mount({id:"vueuc/x-scroll",head:!0,anchorMetaName:ca,ssr:o}),Object.assign({selfRef:e,handleWheel:n},{scrollTo(...i){var y;(y=e.value)===null||y===void 0||y.scrollTo(...i)}})},render(){return f("div",{ref:"selfRef",onScroll:this.onScroll,onWheel:this.disabled?void 0:this.handleWheel,class:"v-x-scroll"},this.$slots)}});var ua=/\s/;function pa(e){for(var n=e.length;n--&&ua.test(e.charAt(n)););return n}var va=/^\s+/;function ha(e){return e&&e.slice(0,pa(e)+1).replace(va,"")}var Ee=NaN,ga=/^[-+]0x[0-9a-f]+$/i,xa=/^0b[01]+$/i,ma=/^0o[0-7]+$/i,ya=parseInt;function je(e){if(typeof e=="number")return e;if(Lt(e))return Ee;if(le(e)){var n=typeof e.valueOf=="function"?e.valueOf():e;e=le(n)?n+"":n}if(typeof e!="string")return e===0?e:+e;e=ha(e);var o=xa.test(e);return o||ma.test(e)?ya(e.slice(2),o?2:8):ga.test(e)?Ee:+e}var ge=function(){return Et.Date.now()},wa="Expected a function",Ca=Math.max,Sa=Math.min;function Ra(e,n,o){var u,i,y,g,p,d,v=0,h=!1,C=!1,_=!0;if(typeof e!="function")throw new TypeError(wa);n=je(n)||0,le(o)&&(h=!!o.leading,C="maxWait"in o,y=C?Ca(je(o.maxWait)||0,n):y,_="trailing"in o?!!o.trailing:_);function x(c){var L=u,X=i;return u=i=void 0,v=c,g=e.apply(X,L),g}function $(c){return v=c,p=setTimeout(B,n),h?x(c):g}function z(c){var L=c-d,X=c-v,G=n-L;return C?Sa(G,y-X):G}function W(c){var L=c-d,X=c-v;return d===void 0||L>=n||L<0||C&&X>=y}function B(){var c=ge();if(W(c))return k(c);p=setTimeout(B,z(c))}function k(c){return p=void 0,_&&u?x(c):(u=i=void 0,g)}function F(){p!==void 0&&clearTimeout(p),v=0,u=d=i=p=void 0}function O(){return p===void 0?g:k(ge())}function w(){var c=ge(),L=W(c);if(u=arguments,i=this,d=c,L){if(p===void 0)return $(d);if(C)return clearTimeout(p),p=setTimeout(B,n),x(d)}return p===void 0&&(p=setTimeout(B,n)),g}return w.cancel=F,w.flush=O,w}var _a="Expected a function";function $a(e,n,o){var u=!0,i=!0;if(typeof e!="function")throw new TypeError(_a);return le(o)&&(u="leading"in o?!!o.leading:u,i="trailing"in o?!!o.trailing:i),Ra(e,n,{leading:u,maxWait:n,trailing:i})}const za=U({name:"Add",render(){return f("svg",{width:"512",height:"512",viewBox:"0 0 512 512",fill:"none",xmlns:"http://www.w3.org/2000/svg"},f("path",{d:"M256 112V400M400 256H112",stroke:"currentColor","stroke-width":"32","stroke-linecap":"round","stroke-linejoin":"round"}))}}),Ce=jt("n-tabs"),Ve={tab:[String,Number,Object,Function],name:{type:[String,Number],required:!0},disabled:Boolean,displayDirective:{type:String,default:"if"},closable:{type:Boolean,default:void 0},tabProps:Object,label:[String,Number,Object,Function]},Ta=U({__TAB_PANE__:!0,name:"TabPane",alias:["TabPanel"],props:Ve,slots:Object,setup(e){const n=He(Ce,null);return n||At("tab-pane","`n-tab-pane` must be placed inside `n-tabs`."),{style:n.paneStyleRef,class:n.paneClassRef,mergedClsPrefix:n.mergedClsPrefixRef}},render(){return f("div",{class:[`${this.mergedClsPrefix}-tab-pane`,this.class],style:this.style},this.$slots)}}),ka=Object.assign({internalLeftPadded:Boolean,internalAddable:Boolean,internalCreatedByPane:Boolean},Ft(Ve,["displayDirective"])),ye=U({__TAB__:!0,inheritAttrs:!1,name:"Tab",props:ka,setup(e){const{mergedClsPrefixRef:n,valueRef:o,typeRef:u,closableRef:i,tabStyleRef:y,addTabStyleRef:g,tabClassRef:p,addTabClassRef:d,tabChangeIdRef:v,onBeforeLeaveRef:h,triggerRef:C,handleAdd:_,activateTab:x,handleClose:$}=He(Ce);return{trigger:C,mergedClosable:V(()=>{if(e.internalAddable)return!1;const{closable:z}=e;return z===void 0?i.value:z}),style:y,addStyle:g,tabClass:p,addTabClass:d,clsPrefix:n,value:o,type:u,handleClose(z){z.stopPropagation(),!e.disabled&&$(e.name)},activateTab(){if(e.disabled)return;if(e.internalAddable){_();return}const{name:z}=e,W=++v.id;if(z!==o.value){const{value:B}=h;B?Promise.resolve(B(e.name,o.value)).then(k=>{k&&v.id===W&&x(z)}):x(z)}}}},render(){const{internalAddable:e,clsPrefix:n,name:o,disabled:u,label:i,tab:y,value:g,mergedClosable:p,trigger:d,$slots:{default:v}}=this,h=i??y;return f("div",{class:`${n}-tabs-tab-wrapper`},this.internalLeftPadded?f("div",{class:`${n}-tabs-tab-pad`}):null,f("div",Object.assign({key:o,"data-name":o,"data-disabled":u?!0:void 0},It({class:[`${n}-tabs-tab`,g===o&&`${n}-tabs-tab--active`,u&&`${n}-tabs-tab--disabled`,p&&`${n}-tabs-tab--closable`,e&&`${n}-tabs-tab--addable`,e?this.addTabClass:this.tabClass],onClick:d==="click"?this.activateTab:void 0,onMouseenter:d==="hover"?this.activateTab:void 0,style:e?this.addStyle:this.style},this.internalCreatedByPane?this.tabProps||{}:this.$attrs)),f("span",{class:`${n}-tabs-tab__label`},e?f(Me,null,f("div",{class:`${n}-tabs-tab__height-placeholder`}," "),f(Ot,{clsPrefix:n},{default:()=>f(za,null)})):v?v():typeof h=="object"?h:Ht(h??o)),p&&this.type==="card"?f(Mt,{clsPrefix:n,class:`${n}-tabs-tab__close`,onClick:this.handleClose,disabled:u}):null))}}),Pa=r("tabs",`
 box-sizing: border-box;
 width: 100%;
 display: flex;
 flex-direction: column;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
`,[l("segment-type",[r("tabs-rail",[S("&.transition-disabled",[r("tabs-capsule",`
 transition: none;
 `)])])]),l("top",[r("tab-pane",`
 padding: var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left);
 `)]),l("left",[r("tab-pane",`
 padding: var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left) var(--n-pane-padding-top);
 `)]),l("left, right",`
 flex-direction: row;
 `,[r("tabs-bar",`
 width: 2px;
 right: 0;
 transition:
 top .2s var(--n-bezier),
 max-height .2s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),r("tabs-tab",`
 padding: var(--n-tab-padding-vertical); 
 `)]),l("right",`
 flex-direction: row-reverse;
 `,[r("tab-pane",`
 padding: var(--n-pane-padding-left) var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom);
 `),r("tabs-bar",`
 left: 0;
 `)]),l("bottom",`
 flex-direction: column-reverse;
 justify-content: flex-end;
 `,[r("tab-pane",`
 padding: var(--n-pane-padding-bottom) var(--n-pane-padding-right) var(--n-pane-padding-top) var(--n-pane-padding-left);
 `),r("tabs-bar",`
 top: 0;
 `)]),r("tabs-rail",`
 position: relative;
 padding: 3px;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 background-color: var(--n-color-segment);
 transition: background-color .3s var(--n-bezier);
 display: flex;
 align-items: center;
 `,[r("tabs-capsule",`
 border-radius: var(--n-tab-border-radius);
 position: absolute;
 pointer-events: none;
 background-color: var(--n-tab-color-segment);
 box-shadow: 0 1px 3px 0 rgba(0, 0, 0, .08);
 transition: transform 0.3s var(--n-bezier);
 `),r("tabs-tab-wrapper",`
 flex-basis: 0;
 flex-grow: 1;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[r("tabs-tab",`
 overflow: hidden;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[l("active",`
 font-weight: var(--n-font-weight-strong);
 color: var(--n-tab-text-color-active);
 `),S("&:hover",`
 color: var(--n-tab-text-color-hover);
 `)])])]),l("flex",[r("tabs-nav",`
 width: 100%;
 position: relative;
 `,[r("tabs-wrapper",`
 width: 100%;
 `,[r("tabs-tab",`
 margin-right: 0;
 `)])])]),r("tabs-nav",`
 box-sizing: border-box;
 line-height: 1.5;
 display: flex;
 transition: border-color .3s var(--n-bezier);
 `,[T("prefix, suffix",`
 display: flex;
 align-items: center;
 `),T("prefix","padding-right: 16px;"),T("suffix","padding-left: 16px;")]),l("top, bottom",[S(">",[r("tabs-nav",[r("tabs-nav-scroll-wrapper",[S("&::before",`
 top: 0;
 bottom: 0;
 left: 0;
 width: 20px;
 `),S("&::after",`
 top: 0;
 bottom: 0;
 right: 0;
 width: 20px;
 `),l("shadow-start",[S("&::before",`
 box-shadow: inset 10px 0 8px -8px rgba(0, 0, 0, .12);
 `)]),l("shadow-end",[S("&::after",`
 box-shadow: inset -10px 0 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),l("left, right",[r("tabs-nav-scroll-content",`
 flex-direction: column;
 `),S(">",[r("tabs-nav",[r("tabs-nav-scroll-wrapper",[S("&::before",`
 top: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),S("&::after",`
 bottom: 0;
 left: 0;
 right: 0;
 height: 20px;
 `),l("shadow-start",[S("&::before",`
 box-shadow: inset 0 10px 8px -8px rgba(0, 0, 0, .12);
 `)]),l("shadow-end",[S("&::after",`
 box-shadow: inset 0 -10px 8px -8px rgba(0, 0, 0, .12);
 `)])])])])]),r("tabs-nav-scroll-wrapper",`
 flex: 1;
 position: relative;
 overflow: hidden;
 `,[r("tabs-nav-y-scroll",`
 height: 100%;
 width: 100%;
 overflow-y: auto; 
 scrollbar-width: none;
 `,[S("&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb",`
 width: 0;
 height: 0;
 display: none;
 `)]),S("&::before, &::after",`
 transition: box-shadow .3s var(--n-bezier);
 pointer-events: none;
 content: "";
 position: absolute;
 z-index: 1;
 `)]),r("tabs-nav-scroll-content",`
 display: flex;
 position: relative;
 min-width: 100%;
 min-height: 100%;
 width: fit-content;
 box-sizing: border-box;
 `),r("tabs-wrapper",`
 display: inline-flex;
 flex-wrap: nowrap;
 position: relative;
 `),r("tabs-tab-wrapper",`
 display: flex;
 flex-wrap: nowrap;
 flex-shrink: 0;
 flex-grow: 0;
 `),r("tabs-tab",`
 cursor: pointer;
 white-space: nowrap;
 flex-wrap: nowrap;
 display: inline-flex;
 align-items: center;
 color: var(--n-tab-text-color);
 font-size: var(--n-tab-font-size);
 background-clip: padding-box;
 padding: var(--n-tab-padding);
 transition:
 box-shadow .3s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[l("disabled",{cursor:"not-allowed"}),T("close",`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),T("label",`
 display: flex;
 align-items: center;
 z-index: 1;
 `)]),r("tabs-bar",`
 position: absolute;
 bottom: 0;
 height: 2px;
 border-radius: 1px;
 background-color: var(--n-bar-color);
 transition:
 left .2s var(--n-bezier),
 max-width .2s var(--n-bezier),
 opacity .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `,[S("&.transition-disabled",`
 transition: none;
 `),l("disabled",`
 background-color: var(--n-tab-text-color-disabled)
 `)]),r("tabs-pane-wrapper",`
 position: relative;
 overflow: hidden;
 transition: max-height .2s var(--n-bezier);
 `),r("tab-pane",`
 color: var(--n-pane-text-color);
 width: 100%;
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 opacity .2s var(--n-bezier);
 left: 0;
 right: 0;
 top: 0;
 `,[S("&.next-transition-leave-active, &.prev-transition-leave-active, &.next-transition-enter-active, &.prev-transition-enter-active",`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 transform .2s var(--n-bezier),
 opacity .2s var(--n-bezier);
 `),S("&.next-transition-leave-active, &.prev-transition-leave-active",`
 position: absolute;
 `),S("&.next-transition-enter-from, &.prev-transition-leave-to",`
 transform: translateX(32px);
 opacity: 0;
 `),S("&.next-transition-leave-to, &.prev-transition-enter-from",`
 transform: translateX(-32px);
 opacity: 0;
 `),S("&.next-transition-leave-from, &.next-transition-enter-to, &.prev-transition-leave-from, &.prev-transition-enter-to",`
 transform: translateX(0);
 opacity: 1;
 `)]),r("tabs-tab-pad",`
 box-sizing: border-box;
 width: var(--n-tab-gap);
 flex-grow: 0;
 flex-shrink: 0;
 `),l("line-type, bar-type",[r("tabs-tab",`
 font-weight: var(--n-tab-font-weight);
 box-sizing: border-box;
 vertical-align: bottom;
 `,[S("&:hover",{color:"var(--n-tab-text-color-hover)"}),l("active",`
 color: var(--n-tab-text-color-active);
 font-weight: var(--n-tab-font-weight-active);
 `),l("disabled",{color:"var(--n-tab-text-color-disabled)"})])]),r("tabs-nav",[l("line-type",[l("top",[T("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 bottom: -1px;
 `)]),l("left",[T("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 right: -1px;
 `)]),l("right",[T("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 left: -1px;
 `)]),l("bottom",[T("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-nav-scroll-content",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-bar",`
 top: -1px;
 `)]),T("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-nav-scroll-content",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-bar",`
 border-radius: 0;
 `)]),l("card-type",[T("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-pad",`
 flex-grow: 1;
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-tab-pad",`
 transition: border-color .3s var(--n-bezier);
 `),r("tabs-tab",`
 font-weight: var(--n-tab-font-weight);
 border: 1px solid var(--n-tab-border-color);
 background-color: var(--n-tab-color);
 box-sizing: border-box;
 position: relative;
 vertical-align: bottom;
 display: flex;
 justify-content: space-between;
 font-size: var(--n-tab-font-size);
 color: var(--n-tab-text-color);
 `,[l("addable",`
 padding-left: 8px;
 padding-right: 8px;
 font-size: 16px;
 justify-content: center;
 `,[T("height-placeholder",`
 width: 0;
 font-size: var(--n-tab-font-size);
 `),Dt("disabled",[S("&:hover",`
 color: var(--n-tab-text-color-hover);
 `)])]),l("closable","padding-right: 8px;"),l("active",`
 background-color: #0000;
 font-weight: var(--n-tab-font-weight-active);
 color: var(--n-tab-text-color-active);
 `),l("disabled","color: var(--n-tab-text-color-disabled);")])]),l("left, right",`
 flex-direction: column; 
 `,[T("prefix, suffix",`
 padding: var(--n-tab-padding-vertical);
 `),r("tabs-wrapper",`
 flex-direction: column;
 `),r("tabs-tab-wrapper",`
 flex-direction: column;
 `,[r("tabs-tab-pad",`
 height: var(--n-tab-gap-vertical);
 width: 100%;
 `)])]),l("top",[l("card-type",[r("tabs-scroll-padding","border-bottom: 1px solid var(--n-tab-border-color);"),T("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-top-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-bottom: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `)])]),l("left",[l("card-type",[r("tabs-scroll-padding","border-right: 1px solid var(--n-tab-border-color);"),T("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-bottom-left-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-right: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `)])]),l("right",[l("card-type",[r("tabs-scroll-padding","border-left: 1px solid var(--n-tab-border-color);"),T("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-top-right-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-left: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `)])]),l("bottom",[l("card-type",[r("tabs-scroll-padding","border-top: 1px solid var(--n-tab-border-color);"),T("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-tab",`
 border-bottom-left-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-top: 1px solid #0000;
 `)]),r("tabs-tab-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `),r("tabs-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `)])])])]),xe=$a,Wa=Object.assign(Object.assign({},Fe.props),{value:[String,Number],defaultValue:[String,Number],trigger:{type:String,default:"click"},type:{type:String,default:"bar"},closable:Boolean,justifyContent:String,size:String,placement:{type:String,default:"top"},tabStyle:[String,Object],tabClass:String,addTabStyle:[String,Object],addTabClass:String,barWidth:Number,paneClass:String,paneStyle:[String,Object],paneWrapperClass:String,paneWrapperStyle:[String,Object],addable:[Boolean,Object],tabsPadding:{type:Number,default:0},animated:Boolean,onBeforeLeave:Function,onAdd:Function,"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onClose:[Function,Array],labelSize:String,activeName:[String,Number],onActiveNameChange:[Function,Array]}),Ba=U({name:"Tabs",props:Wa,slots:Object,setup(e,{slots:n}){var o,u,i,y;const{mergedClsPrefixRef:g,inlineThemeDisabled:p,mergedComponentPropsRef:d}=Nt(e),v=Fe("Tabs","-tabs",Pa,qt,e,g),h=P(null),C=P(null),_=P(null),x=P(null),$=P(null),z=P(null),W=P(!0),B=P(!0),k=Be(e,["labelSize","size"]),F=V(()=>{var t,a;if(k.value)return k.value;const s=(a=(t=d==null?void 0:d.value)===null||t===void 0?void 0:t.Tabs)===null||a===void 0?void 0:a.size;return s||"medium"}),O=Be(e,["activeName","value"]),w=P((u=(o=O.value)!==null&&o!==void 0?o:e.defaultValue)!==null&&u!==void 0?u:n.default?(y=(i=he(n.default())[0])===null||i===void 0?void 0:i.props)===null||y===void 0?void 0:y.name:null),c=oa(O,w),L={id:0},X=V(()=>{if(!(!e.justifyContent||e.type==="card"))return{display:"flex",justifyContent:e.justifyContent}});pe(c,()=>{L.id=0,ne(),Re()});function G(){var t;const{value:a}=c;return a===null?null:(t=h.value)===null||t===void 0?void 0:t.querySelector(`[data-name="${a}"]`)}function Ue(t){if(e.type==="card")return;const{value:a}=C;if(!a)return;const s=a.style.opacity==="0";if(t){const b=`${g.value}-tabs-bar--disabled`,{barWidth:R,placement:j}=e;if(t.dataset.disabled==="true"?a.classList.add(b):a.classList.remove(b),["top","bottom"].includes(j)){if(Se(["top","maxHeight","height"]),typeof R=="number"&&t.offsetWidth>=R){const A=Math.floor((t.offsetWidth-R)/2)+t.offsetLeft;a.style.left=`${A}px`,a.style.maxWidth=`${R}px`}else a.style.left=`${t.offsetLeft}px`,a.style.maxWidth=`${t.offsetWidth}px`;a.style.width="8192px",s&&(a.style.transition="none"),a.offsetWidth,s&&(a.style.transition="",a.style.opacity="1")}else{if(Se(["left","maxWidth","width"]),typeof R=="number"&&t.offsetHeight>=R){const A=Math.floor((t.offsetHeight-R)/2)+t.offsetTop;a.style.top=`${A}px`,a.style.maxHeight=`${R}px`}else a.style.top=`${t.offsetTop}px`,a.style.maxHeight=`${t.offsetHeight}px`;a.style.height="8192px",s&&(a.style.transition="none"),a.offsetHeight,s&&(a.style.transition="",a.style.opacity="1")}}}function Xe(){if(e.type==="card")return;const{value:t}=C;t&&(t.style.opacity="0")}function Se(t){const{value:a}=C;if(a)for(const s of t)a.style[s]=""}function ne(){if(e.type==="card")return;const t=G();t?Ue(t):Xe()}function Re(){var t;const a=(t=$.value)===null||t===void 0?void 0:t.$el;if(!a)return;const s=G();if(!s)return;const{scrollLeft:b,offsetWidth:R}=a,{offsetLeft:j,offsetWidth:A}=s;b>j?a.scrollTo({top:0,left:j,behavior:"smooth"}):j+A>b+R&&a.scrollTo({top:0,left:j+A-R,behavior:"smooth"})}const re=P(null);let ce=0,D=null;function Ge(t){const a=re.value;if(a){ce=t.getBoundingClientRect().height;const s=`${ce}px`,b=()=>{a.style.height=s,a.style.maxHeight=s};D?(b(),D(),D=null):D=b}}function Ke(t){const a=re.value;if(a){const s=t.getBoundingClientRect().height,b=()=>{document.body.offsetHeight,a.style.maxHeight=`${s}px`,a.style.height=`${Math.max(ce,s)}px`};D?(D(),D=null,b()):D=b}}function Ye(){const t=re.value;if(t){t.style.maxHeight="",t.style.height="";const{paneWrapperStyle:a}=e;if(typeof a=="string")t.style.cssText=a;else if(a){const{maxHeight:s,height:b}=a;s!==void 0&&(t.style.maxHeight=s),b!==void 0&&(t.style.height=b)}}}const _e={value:[]},$e=P("next");function qe(t){const a=c.value;let s="next";for(const b of _e.value){if(b===a)break;if(b===t){s="prev";break}}$e.value=s,Je(t)}function Je(t){const{onActiveNameChange:a,onUpdateValue:s,"onUpdate:value":b}=e;a&&ie(a,t),s&&ie(s,t),b&&ie(b,t),w.value=t}function Qe(t){const{onClose:a}=e;a&&ie(a,t)}function ze(){const{value:t}=C;if(!t)return;const a="transition-disabled";t.classList.add(a),ne(),t.classList.remove(a)}const Y=P(null);function be({transitionDisabled:t}){const a=h.value;if(!a)return;t&&a.classList.add("transition-disabled");const s=G();s&&Y.value&&(Y.value.style.width=`${s.offsetWidth}px`,Y.value.style.height=`${s.offsetHeight}px`,Y.value.style.transform=`translateX(${s.offsetLeft-Xt(getComputedStyle(a).paddingLeft)}px)`,t&&Y.value.offsetWidth),t&&a.classList.remove("transition-disabled")}pe([c],()=>{e.type==="segment"&&ve(()=>{be({transitionDisabled:!1})})}),we(()=>{e.type==="segment"&&be({transitionDisabled:!0})});let Te=0;function Ze(t){var a;if(t.contentRect.width===0&&t.contentRect.height===0||Te===t.contentRect.width)return;Te=t.contentRect.width;const{type:s}=e;if((s==="line"||s==="bar")&&ze(),s!=="segment"){const{placement:b}=e;fe((b==="top"||b==="bottom"?(a=$.value)===null||a===void 0?void 0:a.$el:z.value)||null)}}const et=xe(Ze,64);pe([()=>e.justifyContent,()=>e.size],()=>{ve(()=>{const{type:t}=e;(t==="line"||t==="bar")&&ze()})});const q=P(!1);function tt(t){var a;const{target:s,contentRect:{width:b,height:R}}=t,j=s.parentElement.parentElement.offsetWidth,A=s.parentElement.parentElement.offsetHeight,{placement:Q}=e;if(!q.value)Q==="top"||Q==="bottom"?j<b&&(q.value=!0):A<R&&(q.value=!0);else{const{value:ee}=x;if(!ee)return;Q==="top"||Q==="bottom"?j-b>ee.$el.offsetWidth&&(q.value=!1):A-R>ee.$el.offsetHeight&&(q.value=!1)}fe(((a=$.value)===null||a===void 0?void 0:a.$el)||null)}const at=xe(tt,64);function nt(){const{onAdd:t}=e;t&&t(),ve(()=>{const a=G(),{value:s}=$;!a||!s||s.scrollTo({left:a.offsetLeft,top:0,behavior:"smooth"})})}function fe(t){if(!t)return;const{placement:a}=e;if(a==="top"||a==="bottom"){const{scrollLeft:s,scrollWidth:b,offsetWidth:R}=t;W.value=s<=0,B.value=s+R>=b}else{const{scrollTop:s,scrollHeight:b,offsetHeight:R}=t;W.value=s<=0,B.value=s+R>=b}}const rt=xe(t=>{fe(t.target)},64);Qt(Ce,{triggerRef:M(e,"trigger"),tabStyleRef:M(e,"tabStyle"),tabClassRef:M(e,"tabClass"),addTabStyleRef:M(e,"addTabStyle"),addTabClassRef:M(e,"addTabClass"),paneClassRef:M(e,"paneClass"),paneStyleRef:M(e,"paneStyle"),mergedClsPrefixRef:g,typeRef:M(e,"type"),closableRef:M(e,"closable"),valueRef:c,tabChangeIdRef:L,onBeforeLeaveRef:M(e,"onBeforeLeave"),activateTab:qe,handleClose:Qe,handleAdd:nt}),da(()=>{ne(),Re()}),Vt(()=>{const{value:t}=_;if(!t)return;const{value:a}=g,s=`${a}-tabs-nav-scroll-wrapper--shadow-start`,b=`${a}-tabs-nav-scroll-wrapper--shadow-end`;W.value?t.classList.remove(s):t.classList.add(s),B.value?t.classList.remove(b):t.classList.add(b)});const ot={syncBarPosition:()=>{ne()}},st=()=>{be({transitionDisabled:!0})},ke=V(()=>{const{value:t}=F,{type:a}=e,s={card:"Card",bar:"Bar",line:"Line",segment:"Segment"}[a],b=`${t}${s}`,{self:{barColor:R,closeIconColor:j,closeIconColorHover:A,closeIconColorPressed:Q,tabColor:ee,tabBorderColor:it,paneTextColor:lt,tabFontWeight:dt,tabBorderRadius:ct,tabFontWeightActive:bt,colorSegment:ft,fontWeightStrong:ut,tabColorSegment:pt,closeSize:vt,closeIconSize:ht,closeColorHover:gt,closeColorPressed:xt,closeBorderRadius:mt,[H("panePadding",t)]:oe,[H("tabPadding",b)]:yt,[H("tabPaddingVertical",b)]:wt,[H("tabGap",b)]:Ct,[H("tabGap",`${b}Vertical`)]:St,[H("tabTextColor",a)]:Rt,[H("tabTextColorActive",a)]:_t,[H("tabTextColorHover",a)]:$t,[H("tabTextColorDisabled",a)]:zt,[H("tabFontSize",t)]:Tt},common:{cubicBezierEaseInOut:kt}}=v.value;return{"--n-bezier":kt,"--n-color-segment":ft,"--n-bar-color":R,"--n-tab-font-size":Tt,"--n-tab-text-color":Rt,"--n-tab-text-color-active":_t,"--n-tab-text-color-disabled":zt,"--n-tab-text-color-hover":$t,"--n-pane-text-color":lt,"--n-tab-border-color":it,"--n-tab-border-radius":ct,"--n-close-size":vt,"--n-close-icon-size":ht,"--n-close-color-hover":gt,"--n-close-color-pressed":xt,"--n-close-border-radius":mt,"--n-close-icon-color":j,"--n-close-icon-color-hover":A,"--n-close-icon-color-pressed":Q,"--n-tab-color":ee,"--n-tab-font-weight":dt,"--n-tab-font-weight-active":bt,"--n-tab-padding":yt,"--n-tab-padding-vertical":wt,"--n-tab-gap":Ct,"--n-tab-gap-vertical":St,"--n-pane-padding-left":se(oe,"left"),"--n-pane-padding-right":se(oe,"right"),"--n-pane-padding-top":se(oe,"top"),"--n-pane-padding-bottom":se(oe,"bottom"),"--n-font-weight-strong":ut,"--n-tab-color-segment":pt}}),J=p?Ut("tabs",V(()=>`${F.value[0]}${e.type[0]}`),ke,e):void 0;return Object.assign({mergedClsPrefix:g,mergedValue:c,renderedNames:new Set,segmentCapsuleElRef:Y,tabsPaneWrapperRef:re,tabsElRef:h,barElRef:C,addTabInstRef:x,xScrollInstRef:$,scrollWrapperElRef:_,addTabFixed:q,tabWrapperStyle:X,handleNavResize:et,mergedSize:F,handleScroll:rt,handleTabsResize:at,cssVars:p?void 0:ke,themeClass:J==null?void 0:J.themeClass,animationDirection:$e,renderNameListRef:_e,yScrollElRef:z,handleSegmentResize:st,onAnimationBeforeLeave:Ge,onAnimationEnter:Ke,onAnimationAfterEnter:Ye,onRender:J==null?void 0:J.onRender},ot)},render(){const{mergedClsPrefix:e,type:n,placement:o,addTabFixed:u,addable:i,mergedSize:y,renderNameListRef:g,onRender:p,paneWrapperClass:d,paneWrapperStyle:v,$slots:{default:h,prefix:C,suffix:_}}=this;p==null||p();const x=h?he(h()).filter(w=>w.type.__TAB_PANE__===!0):[],$=h?he(h()).filter(w=>w.type.__TAB__===!0):[],z=!$.length,W=n==="card",B=n==="segment",k=!W&&!B&&this.justifyContent;g.value=[];const F=()=>{const w=f("div",{style:this.tabWrapperStyle,class:`${e}-tabs-wrapper`},k?null:f("div",{class:`${e}-tabs-scroll-padding`,style:o==="top"||o==="bottom"?{width:`${this.tabsPadding}px`}:{height:`${this.tabsPadding}px`}}),z?x.map((c,L)=>(g.value.push(c.props.name),me(f(ye,Object.assign({},c.props,{internalCreatedByPane:!0,internalLeftPadded:L!==0&&(!k||k==="center"||k==="start"||k==="end")}),c.children?{default:c.children.tab}:void 0)))):$.map((c,L)=>(g.value.push(c.props.name),me(L!==0&&!k?Oe(c):c))),!u&&i&&W?Ie(i,(z?x.length:$.length)!==0):null,k?null:f("div",{class:`${e}-tabs-scroll-padding`,style:{width:`${this.tabsPadding}px`}}));return f("div",{ref:"tabsElRef",class:`${e}-tabs-nav-scroll-content`},W&&i?f(ue,{onResize:this.handleTabsResize},{default:()=>w}):w,W?f("div",{class:`${e}-tabs-pad`}):null,W?null:f("div",{ref:"barElRef",class:`${e}-tabs-bar`}))},O=B?"top":o;return f("div",{class:[`${e}-tabs`,this.themeClass,`${e}-tabs--${n}-type`,`${e}-tabs--${y}-size`,k&&`${e}-tabs--flex`,`${e}-tabs--${O}`],style:this.cssVars},f("div",{class:[`${e}-tabs-nav--${n}-type`,`${e}-tabs-nav--${O}`,`${e}-tabs-nav`]},We(C,w=>w&&f("div",{class:`${e}-tabs-nav__prefix`},w)),B?f(ue,{onResize:this.handleSegmentResize},{default:()=>f("div",{class:`${e}-tabs-rail`,ref:"tabsElRef"},f("div",{class:`${e}-tabs-capsule`,ref:"segmentCapsuleElRef"},f("div",{class:`${e}-tabs-wrapper`},f("div",{class:`${e}-tabs-tab`}))),z?x.map((w,c)=>(g.value.push(w.props.name),f(ye,Object.assign({},w.props,{internalCreatedByPane:!0,internalLeftPadded:c!==0}),w.children?{default:w.children.tab}:void 0))):$.map((w,c)=>(g.value.push(w.props.name),c===0?w:Oe(w))))}):f(ue,{onResize:this.handleNavResize},{default:()=>f("div",{class:`${e}-tabs-nav-scroll-wrapper`,ref:"scrollWrapperElRef"},["top","bottom"].includes(O)?f(fa,{ref:"xScrollInstRef",onScroll:this.handleScroll},{default:F}):f("div",{class:`${e}-tabs-nav-y-scroll`,onScroll:this.handleScroll,ref:"yScrollElRef"},F()))}),u&&i&&W?Ie(i,!0):null,We(_,w=>w&&f("div",{class:`${e}-tabs-nav__suffix`},w))),z&&(this.animated&&(O==="top"||O==="bottom")?f("div",{ref:"tabsPaneWrapperRef",style:v,class:[`${e}-tabs-pane-wrapper`,d]},Ae(x,this.mergedValue,this.renderedNames,this.onAnimationBeforeLeave,this.onAnimationEnter,this.onAnimationAfterEnter,this.animationDirection)):Ae(x,this.mergedValue,this.renderedNames)))}});function Ae(e,n,o,u,i,y,g){const p=[];return e.forEach(d=>{const{name:v,displayDirective:h,"display-directive":C}=d.props,_=$=>h===$||C===$,x=n===v;if(d.key!==void 0&&(d.key=v),x||_("show")||_("show:lazy")&&o.has(v)){o.has(v)||o.add(v);const $=!_("if");p.push($?Gt(d,[[Jt,x]]):d)}}),g?f(Kt,{name:`${g}-transition`,onBeforeLeave:u,onEnter:i,onAfterEnter:y},{default:()=>p}):p}function Ie(e,n){return f(ye,{ref:"addTabInstRef",key:"__addable",name:"__addable",internalCreatedByPane:!0,internalAddable:!0,internalLeftPadded:n,disabled:typeof e=="object"&&e.disabled})}function Oe(e){const n=Yt(e);return n.props?n.props.internalLeftPadded=!0:n.props={internalLeftPadded:!0},n}function me(e){return Array.isArray(e.dynamicProps)?e.dynamicProps.includes("internalLeftPadded")||e.dynamicProps.push("internalLeftPadded"):e.dynamicProps=["internalLeftPadded"],e}function La(){const{copy:e,copied:n}=Zt(),o=P(!1);async function u(y){await e(y),setTimeout(()=>n.value=!1,2e3)}function i(y,g){const p=new Blob([y],{type:"text/markdown;charset=utf-8"}),d=URL.createObjectURL(p),v=document.createElement("a");v.href=d,v.download=`${g}.md`,v.click(),URL.revokeObjectURL(d)}return{copyContent:u,downloadMarkdown:i,copied:n,downloading:o}}const Ea={class:"flex items-center justify-between px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]"},ja={class:"flex items-center gap-3"},Aa={class:"text-xl"},Ia={class:"heading-section !mb-0"},Oa={class:"text-xs text-muted mt-0.5"},Ha={key:0,class:"flex gap-1"},Ma={class:"p-6"},Fa={key:0,class:"prose-content text-sm max-h-[600px] overflow-y-auto"},Da={key:1,class:"flex flex-col items-center py-12 text-dim gap-3"},Na={key:2,class:"flex flex-col items-center py-12 text-muted gap-2"},Va=U({__name:"ContentPanel",props:{channel:{},label:{},icon:{},content:{},loading:{type:Boolean}},setup(e){const n=e,{copyContent:o,downloadMarkdown:u,copied:i}=La(),y=V(()=>`ribbon-${n.channel}`),g=V(()=>({gongzhonghao:{color:"var(--ch-gongzhonghao)",description:"深度长文 · 专业调性"},zhihu:{color:"var(--ch-zhihu)",description:"知识分享 · 理性洞察"},xiaohongshu:{color:"var(--ch-xiaohongshu)",description:"种草笔记 · 视觉引导"}})[n.channel]??{color:"var(--accent)",description:""});return(p,d)=>{const v=Ne;return E(),I("div",{class:De(["card !p-0 overflow-hidden animate-enter",y.value])},[m("div",Ea,[m("div",ja,[m("span",Aa,K(e.icon),1),m("div",null,[m("h3",Ia,K(e.label),1),m("p",Oa,K(g.value.description),1)])]),e.content?(E(),I("div",Ha,[m("button",{class:"btn-ghost text-xs !px-3 !py-1.5",onClick:d[0]||(d[0]=h=>N(o)(e.content))},K(N(i)?"✓ 已复制":"📋 复制"),1),m("button",{class:"btn-ghost text-xs !px-3 !py-1.5",onClick:d[1]||(d[1]=h=>N(u)(e.content,e.channel))}," 📥 下载 ")])):ea("",!0)]),m("div",Ma,[te(v,{show:e.loading},{default:de(()=>[e.content?(E(),I("div",Fa,K(e.content),1)):e.loading?(E(),I("div",Da,[...d[2]||(d[2]=[m("div",{class:"w-12 h-12 skeleton rounded-full"},null,-1),m("div",{class:"w-48 h-3 skeleton"},null,-1)])])):(E(),I("div",Na,[...d[3]||(d[3]=[m("span",{class:"text-2xl opacity-40"},"📝",-1),m("p",{class:"text-sm"},"等待生成",-1)])]))]),_:1},8,["show"])])],2)}}}),Ua={class:"card !p-0 overflow-hidden ribbon-review animate-enter"},Xa={class:"p-6"},Ga={key:0,class:"prose-content text-sm max-h-[600px] overflow-y-auto"},Ka={key:1,class:"flex flex-col items-center py-12 text-dim gap-3"},Ya={key:2,class:"flex flex-col items-center py-12 text-muted gap-2"},qa=U({__name:"ReviewReport",props:{report:{},loading:{type:Boolean}},setup(e){return(n,o)=>{const u=Ne;return E(),I("div",Ua,[o[2]||(o[2]=m("div",{class:"flex items-center gap-3 px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]"},[m("span",{class:"text-xl"},"🔍"),m("div",null,[m("h3",{class:"heading-section !mb-0"},"审校报告"),m("p",{class:"text-xs text-muted mt-0.5"},"质量检查 · 一致性校验")])],-1)),m("div",Xa,[te(u,{show:e.loading},{default:de(()=>[e.report?(E(),I("div",Ga,K(e.report),1)):e.loading?(E(),I("div",Ka,[...o[0]||(o[0]=[m("div",{class:"w-12 h-12 skeleton rounded-full"},null,-1),m("div",{class:"w-48 h-3 skeleton"},null,-1)])])):(E(),I("div",Ya,[...o[1]||(o[1]=[m("span",{class:"text-2xl opacity-40"},"✅",-1),m("p",{class:"text-sm"},"等待审校",-1)])]))]),_:1},8,["show"])])])}}}),Ja={class:"h-full overflow-y-auto"},Qa={class:"max-w-3xl mx-auto px-8 py-10 space-y-6"},Za={class:"flex items-center justify-between animate-enter"},en={class:"pt-5"},rn=U({__name:"Preview",setup(e){const n=na(),o=ta(),u=aa();n.params.projectId;const i=P("gongzhonghao"),y=[{key:"gongzhonghao",label:"公众号",icon:"📰"},{key:"zhihu",label:"知乎",icon:"💡"},{key:"xiaohongshu",label:"小红书",icon:"✨"},{key:"review",label:"审校报告",icon:"🔍"}];we(async()=>{u.connect(),await o.refresh()});function g(v){var h,C,_;return((_=(C=(h=o.status)==null?void 0:h.contents)==null?void 0:C[v])==null?void 0:_.full_content)??null}function p(){var v,h;return((h=(v=o.status)==null?void 0:v.review_report)==null?void 0:h.full_content)??null}const d=V(()=>({generating:{cls:"tag-warning",text:"生成中"},done:{cls:"tag-success",text:"已完成"},review:{cls:"tag-warning",text:"审校中"}})[o.stage]??{cls:"tag-accent",text:"等待中"});return(v,h)=>{const C=Ta,_=Ba;return E(),I("div",Ja,[m("div",Qa,[m("div",Za,[h[1]||(h[1]=m("div",null,[m("h2",{class:"heading-display text-2xl"},"内容预览"),m("p",{class:"text-sm text-dim mt-1"},"三篇内容并行生成 · 审校完成后可导出")],-1)),m("span",{class:De(N(d).cls)},K(N(d).text),3)]),te(ia),te(_,{value:i.value,"onUpdate:value":h[0]||(h[0]=x=>i.value=x),type:"line",animated:"",class:"animate-enter stagger-2"},{default:de(()=>[(E(),I(Me,null,ra(y,x=>te(C,{key:x.key,name:x.key,tab:`${x.icon} ${x.label}`},{default:de(()=>[m("div",en,[x.key==="review"?(E(),Pe(qa,{key:0,report:p(),loading:N(o).stage==="generating"||N(o).stage==="review"},null,8,["report","loading"])):(E(),Pe(Va,{key:1,channel:x.key,label:x.label,icon:x.icon,content:g(x.key),loading:N(o).stage==="generating"&&!g(x.key)},null,8,["channel","label","icon","content","loading"]))])]),_:2},1032,["name","tab"])),64))]),_:1},8,["value"])])])}}});export{rn as default};
