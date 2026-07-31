import{d as U,h as f,r as P,_ as zt,aB as kt,aj as se,a2 as Pt,c as Wt,i as je,aO as Bt,at as Lt,I as Ie,aH as Et,aP as At,aQ as jt,q as V,aR as It,b as n,f as l,j as S,e as z,k as Ot,aL as be,u as Ht,l as Oe,w as fe,B as He,ar as Mt,p as Ft,aS as Dt,X as Nt,aT as Vt,aw as Ut,aU as Xt,$ as ue,s as H,aN as re,av as Gt,v as Kt,t as M,aV as Yt,D as E,E as I,P as Me,F as m,K,N,L as qt,G as ee,H as ie,O as Jt,aA as Qt,J as Zt,R as Te}from"./index-CDIvh3Vh.js";import{f as pe,r as ze,u as ea,d as ke,c as oe,_ as Fe,b as ta}from"./ws-CMOh3obd.js";import{c as aa,a as Pe,o as na,_ as ra}from"./ProgressTimeline.vue_vue_type_script_setup_true_lang-CtqwQL8h.js";const oa=Pe(".v-x-scroll",{overflow:"auto",scrollbarWidth:"none"},[Pe("&::-webkit-scrollbar",{width:0,height:0})]),sa=U({name:"XScroll",props:{disabled:Boolean,onScroll:Function},setup(){const e=P(null);function r(i){!(i.currentTarget.offsetWidth<i.currentTarget.scrollWidth)||i.deltaY===0||(i.currentTarget.scrollLeft+=i.deltaY+i.deltaX,i.preventDefault())}const o=zt();return oa.mount({id:"vueuc/x-scroll",head:!0,anchorMetaName:aa,ssr:o}),Object.assign({selfRef:e,handleWheel:r},{scrollTo(...i){var y;(y=e.value)===null||y===void 0||y.scrollTo(...i)}})},render(){return f("div",{ref:"selfRef",onScroll:this.onScroll,onWheel:this.disabled?void 0:this.handleWheel,class:"v-x-scroll"},this.$slots)}});var ia=/\s/;function la(e){for(var r=e.length;r--&&ia.test(e.charAt(r)););return r}var da=/^\s+/;function ca(e){return e&&e.slice(0,la(e)+1).replace(da,"")}var We=NaN,ba=/^[-+]0x[0-9a-f]+$/i,fa=/^0b[01]+$/i,ua=/^0o[0-7]+$/i,pa=parseInt;function Be(e){if(typeof e=="number")return e;if(kt(e))return We;if(se(e)){var r=typeof e.valueOf=="function"?e.valueOf():e;e=se(r)?r+"":r}if(typeof e!="string")return e===0?e:+e;e=ca(e);var o=fa.test(e);return o||ua.test(e)?pa(e.slice(2),o?2:8):ba.test(e)?We:+e}var ve=function(){return Pt.Date.now()},va="Expected a function",ha=Math.max,ga=Math.min;function xa(e,r,o){var u,i,y,g,p,d,v=0,h=!1,C=!1,_=!0;if(typeof e!="function")throw new TypeError(va);r=Be(r)||0,se(o)&&(h=!!o.leading,C="maxWait"in o,y=C?ha(Be(o.maxWait)||0,r):y,_="trailing"in o?!!o.trailing:_);function x(c){var L=u,X=i;return u=i=void 0,v=c,g=e.apply(X,L),g}function $(c){return v=c,p=setTimeout(B,r),h?x(c):g}function T(c){var L=c-d,X=c-v,G=r-L;return C?ga(G,y-X):G}function W(c){var L=c-d,X=c-v;return d===void 0||L>=r||L<0||C&&X>=y}function B(){var c=ve();if(W(c))return k(c);p=setTimeout(B,T(c))}function k(c){return p=void 0,_&&u?x(c):(u=i=void 0,g)}function F(){p!==void 0&&clearTimeout(p),v=0,u=d=i=p=void 0}function O(){return p===void 0?g:k(ve())}function w(){var c=ve(),L=W(c);if(u=arguments,i=this,d=c,L){if(p===void 0)return $(d);if(C)return clearTimeout(p),p=setTimeout(B,r),x(d)}return p===void 0&&(p=setTimeout(B,r)),g}return w.cancel=F,w.flush=O,w}var ma="Expected a function";function ya(e,r,o){var u=!0,i=!0;if(typeof e!="function")throw new TypeError(ma);return se(o)&&(u="leading"in o?!!o.leading:u,i="trailing"in o?!!o.trailing:i),xa(e,r,{leading:u,maxWait:r,trailing:i})}const wa=U({name:"Add",render(){return f("svg",{width:"512",height:"512",viewBox:"0 0 512 512",fill:"none",xmlns:"http://www.w3.org/2000/svg"},f("path",{d:"M256 112V400M400 256H112",stroke:"currentColor","stroke-width":"32","stroke-linecap":"round","stroke-linejoin":"round"}))}}),me=Wt("n-tabs"),De={tab:[String,Number,Object,Function],name:{type:[String,Number],required:!0},disabled:Boolean,displayDirective:{type:String,default:"if"},closable:{type:Boolean,default:void 0},tabProps:Object,label:[String,Number,Object,Function]},Ca=U({__TAB_PANE__:!0,name:"TabPane",alias:["TabPanel"],props:De,slots:Object,setup(e){const r=je(me,null);return r||Bt("tab-pane","`n-tab-pane` must be placed inside `n-tabs`."),{style:r.paneStyleRef,class:r.paneClassRef,mergedClsPrefix:r.mergedClsPrefixRef}},render(){return f("div",{class:[`${this.mergedClsPrefix}-tab-pane`,this.class],style:this.style},this.$slots)}}),Sa=Object.assign({internalLeftPadded:Boolean,internalAddable:Boolean,internalCreatedByPane:Boolean},It(De,["displayDirective"])),xe=U({__TAB__:!0,inheritAttrs:!1,name:"Tab",props:Sa,setup(e){const{mergedClsPrefixRef:r,valueRef:o,typeRef:u,closableRef:i,tabStyleRef:y,addTabStyleRef:g,tabClassRef:p,addTabClassRef:d,tabChangeIdRef:v,onBeforeLeaveRef:h,triggerRef:C,handleAdd:_,activateTab:x,handleClose:$}=je(me);return{trigger:C,mergedClosable:V(()=>{if(e.internalAddable)return!1;const{closable:T}=e;return T===void 0?i.value:T}),style:y,addStyle:g,tabClass:p,addTabClass:d,clsPrefix:r,value:o,type:u,handleClose(T){T.stopPropagation(),!e.disabled&&$(e.name)},activateTab(){if(e.disabled)return;if(e.internalAddable){_();return}const{name:T}=e,W=++v.id;if(T!==o.value){const{value:B}=h;B?Promise.resolve(B(e.name,o.value)).then(k=>{k&&v.id===W&&x(T)}):x(T)}}}},render(){const{internalAddable:e,clsPrefix:r,name:o,disabled:u,label:i,tab:y,value:g,mergedClosable:p,trigger:d,$slots:{default:v}}=this,h=i??y;return f("div",{class:`${r}-tabs-tab-wrapper`},this.internalLeftPadded?f("div",{class:`${r}-tabs-tab-pad`}):null,f("div",Object.assign({key:o,"data-name":o,"data-disabled":u?!0:void 0},Lt({class:[`${r}-tabs-tab`,g===o&&`${r}-tabs-tab--active`,u&&`${r}-tabs-tab--disabled`,p&&`${r}-tabs-tab--closable`,e&&`${r}-tabs-tab--addable`,e?this.addTabClass:this.tabClass],onClick:d==="click"?this.activateTab:void 0,onMouseenter:d==="hover"?this.activateTab:void 0,style:e?this.addStyle:this.style},this.internalCreatedByPane?this.tabProps||{}:this.$attrs)),f("span",{class:`${r}-tabs-tab__label`},e?f(Ie,null,f("div",{class:`${r}-tabs-tab__height-placeholder`}," "),f(Et,{clsPrefix:r},{default:()=>f(wa,null)})):v?v():typeof h=="object"?h:At(h??o)),p&&this.type==="card"?f(jt,{clsPrefix:r,class:`${r}-tabs-tab__close`,onClick:this.handleClose,disabled:u}):null))}}),Ra=n("tabs",`
 box-sizing: border-box;
 width: 100%;
 display: flex;
 flex-direction: column;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
`,[l("segment-type",[n("tabs-rail",[S("&.transition-disabled",[n("tabs-capsule",`
 transition: none;
 `)])])]),l("top",[n("tab-pane",`
 padding: var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left);
 `)]),l("left",[n("tab-pane",`
 padding: var(--n-pane-padding-right) var(--n-pane-padding-bottom) var(--n-pane-padding-left) var(--n-pane-padding-top);
 `)]),l("left, right",`
 flex-direction: row;
 `,[n("tabs-bar",`
 width: 2px;
 right: 0;
 transition:
 top .2s var(--n-bezier),
 max-height .2s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),n("tabs-tab",`
 padding: var(--n-tab-padding-vertical); 
 `)]),l("right",`
 flex-direction: row-reverse;
 `,[n("tab-pane",`
 padding: var(--n-pane-padding-left) var(--n-pane-padding-top) var(--n-pane-padding-right) var(--n-pane-padding-bottom);
 `),n("tabs-bar",`
 left: 0;
 `)]),l("bottom",`
 flex-direction: column-reverse;
 justify-content: flex-end;
 `,[n("tab-pane",`
 padding: var(--n-pane-padding-bottom) var(--n-pane-padding-right) var(--n-pane-padding-top) var(--n-pane-padding-left);
 `),n("tabs-bar",`
 top: 0;
 `)]),n("tabs-rail",`
 position: relative;
 padding: 3px;
 border-radius: var(--n-tab-border-radius);
 width: 100%;
 background-color: var(--n-color-segment);
 transition: background-color .3s var(--n-bezier);
 display: flex;
 align-items: center;
 `,[n("tabs-capsule",`
 border-radius: var(--n-tab-border-radius);
 position: absolute;
 pointer-events: none;
 background-color: var(--n-tab-color-segment);
 box-shadow: 0 1px 3px 0 rgba(0, 0, 0, .08);
 transition: transform 0.3s var(--n-bezier);
 `),n("tabs-tab-wrapper",`
 flex-basis: 0;
 flex-grow: 1;
 display: flex;
 align-items: center;
 justify-content: center;
 `,[n("tabs-tab",`
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
 `)])])]),l("flex",[n("tabs-nav",`
 width: 100%;
 position: relative;
 `,[n("tabs-wrapper",`
 width: 100%;
 `,[n("tabs-tab",`
 margin-right: 0;
 `)])])]),n("tabs-nav",`
 box-sizing: border-box;
 line-height: 1.5;
 display: flex;
 transition: border-color .3s var(--n-bezier);
 `,[z("prefix, suffix",`
 display: flex;
 align-items: center;
 `),z("prefix","padding-right: 16px;"),z("suffix","padding-left: 16px;")]),l("top, bottom",[S(">",[n("tabs-nav",[n("tabs-nav-scroll-wrapper",[S("&::before",`
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
 `)])])])])]),l("left, right",[n("tabs-nav-scroll-content",`
 flex-direction: column;
 `),S(">",[n("tabs-nav",[n("tabs-nav-scroll-wrapper",[S("&::before",`
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
 `)])])])])]),n("tabs-nav-scroll-wrapper",`
 flex: 1;
 position: relative;
 overflow: hidden;
 `,[n("tabs-nav-y-scroll",`
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
 `)]),n("tabs-nav-scroll-content",`
 display: flex;
 position: relative;
 min-width: 100%;
 min-height: 100%;
 width: fit-content;
 box-sizing: border-box;
 `),n("tabs-wrapper",`
 display: inline-flex;
 flex-wrap: nowrap;
 position: relative;
 `),n("tabs-tab-wrapper",`
 display: flex;
 flex-wrap: nowrap;
 flex-shrink: 0;
 flex-grow: 0;
 `),n("tabs-tab",`
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
 `,[l("disabled",{cursor:"not-allowed"}),z("close",`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),z("label",`
 display: flex;
 align-items: center;
 z-index: 1;
 `)]),n("tabs-bar",`
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
 `)]),n("tabs-pane-wrapper",`
 position: relative;
 overflow: hidden;
 transition: max-height .2s var(--n-bezier);
 `),n("tab-pane",`
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
 `)]),n("tabs-tab-pad",`
 box-sizing: border-box;
 width: var(--n-tab-gap);
 flex-grow: 0;
 flex-shrink: 0;
 `),l("line-type, bar-type",[n("tabs-tab",`
 font-weight: var(--n-tab-font-weight);
 box-sizing: border-box;
 vertical-align: bottom;
 `,[S("&:hover",{color:"var(--n-tab-text-color-hover)"}),l("active",`
 color: var(--n-tab-text-color-active);
 font-weight: var(--n-tab-font-weight-active);
 `),l("disabled",{color:"var(--n-tab-text-color-disabled)"})])]),n("tabs-nav",[l("line-type",[l("top",[z("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),n("tabs-nav-scroll-content",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),n("tabs-bar",`
 bottom: -1px;
 `)]),l("left",[z("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),n("tabs-nav-scroll-content",`
 border-right: 1px solid var(--n-tab-border-color);
 `),n("tabs-bar",`
 right: -1px;
 `)]),l("right",[z("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),n("tabs-nav-scroll-content",`
 border-left: 1px solid var(--n-tab-border-color);
 `),n("tabs-bar",`
 left: -1px;
 `)]),l("bottom",[z("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),n("tabs-nav-scroll-content",`
 border-top: 1px solid var(--n-tab-border-color);
 `),n("tabs-bar",`
 top: -1px;
 `)]),z("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),n("tabs-nav-scroll-content",`
 transition: border-color .3s var(--n-bezier);
 `),n("tabs-bar",`
 border-radius: 0;
 `)]),l("card-type",[z("prefix, suffix",`
 transition: border-color .3s var(--n-bezier);
 `),n("tabs-pad",`
 flex-grow: 1;
 transition: border-color .3s var(--n-bezier);
 `),n("tabs-tab-pad",`
 transition: border-color .3s var(--n-bezier);
 `),n("tabs-tab",`
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
 `,[z("height-placeholder",`
 width: 0;
 font-size: var(--n-tab-font-size);
 `),Ot("disabled",[S("&:hover",`
 color: var(--n-tab-text-color-hover);
 `)])]),l("closable","padding-right: 8px;"),l("active",`
 background-color: #0000;
 font-weight: var(--n-tab-font-weight-active);
 color: var(--n-tab-text-color-active);
 `),l("disabled","color: var(--n-tab-text-color-disabled);")])]),l("left, right",`
 flex-direction: column; 
 `,[z("prefix, suffix",`
 padding: var(--n-tab-padding-vertical);
 `),n("tabs-wrapper",`
 flex-direction: column;
 `),n("tabs-tab-wrapper",`
 flex-direction: column;
 `,[n("tabs-tab-pad",`
 height: var(--n-tab-gap-vertical);
 width: 100%;
 `)])]),l("top",[l("card-type",[n("tabs-scroll-padding","border-bottom: 1px solid var(--n-tab-border-color);"),z("prefix, suffix",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),n("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-top-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-bottom: 1px solid #0000;
 `)]),n("tabs-tab-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `),n("tabs-pad",`
 border-bottom: 1px solid var(--n-tab-border-color);
 `)])]),l("left",[l("card-type",[n("tabs-scroll-padding","border-right: 1px solid var(--n-tab-border-color);"),z("prefix, suffix",`
 border-right: 1px solid var(--n-tab-border-color);
 `),n("tabs-tab",`
 border-top-left-radius: var(--n-tab-border-radius);
 border-bottom-left-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-right: 1px solid #0000;
 `)]),n("tabs-tab-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `),n("tabs-pad",`
 border-right: 1px solid var(--n-tab-border-color);
 `)])]),l("right",[l("card-type",[n("tabs-scroll-padding","border-left: 1px solid var(--n-tab-border-color);"),z("prefix, suffix",`
 border-left: 1px solid var(--n-tab-border-color);
 `),n("tabs-tab",`
 border-top-right-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-left: 1px solid #0000;
 `)]),n("tabs-tab-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `),n("tabs-pad",`
 border-left: 1px solid var(--n-tab-border-color);
 `)])]),l("bottom",[l("card-type",[n("tabs-scroll-padding","border-top: 1px solid var(--n-tab-border-color);"),z("prefix, suffix",`
 border-top: 1px solid var(--n-tab-border-color);
 `),n("tabs-tab",`
 border-bottom-left-radius: var(--n-tab-border-radius);
 border-bottom-right-radius: var(--n-tab-border-radius);
 `,[l("active",`
 border-top: 1px solid #0000;
 `)]),n("tabs-tab-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `),n("tabs-pad",`
 border-top: 1px solid var(--n-tab-border-color);
 `)])])])]),he=ya,_a=Object.assign(Object.assign({},Oe.props),{value:[String,Number],defaultValue:[String,Number],trigger:{type:String,default:"click"},type:{type:String,default:"bar"},closable:Boolean,justifyContent:String,size:String,placement:{type:String,default:"top"},tabStyle:[String,Object],tabClass:String,addTabStyle:[String,Object],addTabClass:String,barWidth:Number,paneClass:String,paneStyle:[String,Object],paneWrapperClass:String,paneWrapperStyle:[String,Object],addable:[Boolean,Object],tabsPadding:{type:Number,default:0},animated:Boolean,onBeforeLeave:Function,onAdd:Function,"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onClose:[Function,Array],labelSize:String,activeName:[String,Number],onActiveNameChange:[Function,Array]}),$a=U({name:"Tabs",props:_a,slots:Object,setup(e,{slots:r}){var o,u,i,y;const{mergedClsPrefixRef:g,inlineThemeDisabled:p,mergedComponentPropsRef:d}=Ht(e),v=Oe("Tabs","-tabs",Ra,Xt,e,g),h=P(null),C=P(null),_=P(null),x=P(null),$=P(null),T=P(null),W=P(!0),B=P(!0),k=ke(e,["labelSize","size"]),F=V(()=>{var t,a;if(k.value)return k.value;const s=(a=(t=d==null?void 0:d.value)===null||t===void 0?void 0:t.Tabs)===null||a===void 0?void 0:a.size;return s||"medium"}),O=ke(e,["activeName","value"]),w=P((u=(o=O.value)!==null&&o!==void 0?o:e.defaultValue)!==null&&u!==void 0?u:r.default?(y=(i=pe(r.default())[0])===null||i===void 0?void 0:i.props)===null||y===void 0?void 0:y.name:null),c=ea(O,w),L={id:0},X=V(()=>{if(!(!e.justifyContent||e.type==="card"))return{display:"flex",justifyContent:e.justifyContent}});fe(c,()=>{L.id=0,te(),we()});function G(){var t;const{value:a}=c;return a===null?null:(t=h.value)===null||t===void 0?void 0:t.querySelector(`[data-name="${a}"]`)}function Ne(t){if(e.type==="card")return;const{value:a}=C;if(!a)return;const s=a.style.opacity==="0";if(t){const b=`${g.value}-tabs-bar--disabled`,{barWidth:R,placement:A}=e;if(t.dataset.disabled==="true"?a.classList.add(b):a.classList.remove(b),["top","bottom"].includes(A)){if(ye(["top","maxHeight","height"]),typeof R=="number"&&t.offsetWidth>=R){const j=Math.floor((t.offsetWidth-R)/2)+t.offsetLeft;a.style.left=`${j}px`,a.style.maxWidth=`${R}px`}else a.style.left=`${t.offsetLeft}px`,a.style.maxWidth=`${t.offsetWidth}px`;a.style.width="8192px",s&&(a.style.transition="none"),a.offsetWidth,s&&(a.style.transition="",a.style.opacity="1")}else{if(ye(["left","maxWidth","width"]),typeof R=="number"&&t.offsetHeight>=R){const j=Math.floor((t.offsetHeight-R)/2)+t.offsetTop;a.style.top=`${j}px`,a.style.maxHeight=`${R}px`}else a.style.top=`${t.offsetTop}px`,a.style.maxHeight=`${t.offsetHeight}px`;a.style.height="8192px",s&&(a.style.transition="none"),a.offsetHeight,s&&(a.style.transition="",a.style.opacity="1")}}}function Ve(){if(e.type==="card")return;const{value:t}=C;t&&(t.style.opacity="0")}function ye(t){const{value:a}=C;if(a)for(const s of t)a.style[s]=""}function te(){if(e.type==="card")return;const t=G();t?Ne(t):Ve()}function we(){var t;const a=(t=$.value)===null||t===void 0?void 0:t.$el;if(!a)return;const s=G();if(!s)return;const{scrollLeft:b,offsetWidth:R}=a,{offsetLeft:A,offsetWidth:j}=s;b>A?a.scrollTo({top:0,left:A,behavior:"smooth"}):A+j>b+R&&a.scrollTo({top:0,left:A+j-R,behavior:"smooth"})}const ae=P(null);let le=0,D=null;function Ue(t){const a=ae.value;if(a){le=t.getBoundingClientRect().height;const s=`${le}px`,b=()=>{a.style.height=s,a.style.maxHeight=s};D?(b(),D(),D=null):D=b}}function Xe(t){const a=ae.value;if(a){const s=t.getBoundingClientRect().height,b=()=>{document.body.offsetHeight,a.style.maxHeight=`${s}px`,a.style.height=`${Math.max(le,s)}px`};D?(D(),D=null,b()):D=b}}function Ge(){const t=ae.value;if(t){t.style.maxHeight="",t.style.height="";const{paneWrapperStyle:a}=e;if(typeof a=="string")t.style.cssText=a;else if(a){const{maxHeight:s,height:b}=a;s!==void 0&&(t.style.maxHeight=s),b!==void 0&&(t.style.height=b)}}}const Ce={value:[]},Se=P("next");function Ke(t){const a=c.value;let s="next";for(const b of Ce.value){if(b===a)break;if(b===t){s="prev";break}}Se.value=s,Ye(t)}function Ye(t){const{onActiveNameChange:a,onUpdateValue:s,"onUpdate:value":b}=e;a&&oe(a,t),s&&oe(s,t),b&&oe(b,t),w.value=t}function qe(t){const{onClose:a}=e;a&&oe(a,t)}function Re(){const{value:t}=C;if(!t)return;const a="transition-disabled";t.classList.add(a),te(),t.classList.remove(a)}const Y=P(null);function de({transitionDisabled:t}){const a=h.value;if(!a)return;t&&a.classList.add("transition-disabled");const s=G();s&&Y.value&&(Y.value.style.width=`${s.offsetWidth}px`,Y.value.style.height=`${s.offsetHeight}px`,Y.value.style.transform=`translateX(${s.offsetLeft-Dt(getComputedStyle(a).paddingLeft)}px)`,t&&Y.value.offsetWidth),t&&a.classList.remove("transition-disabled")}fe([c],()=>{e.type==="segment"&&ue(()=>{de({transitionDisabled:!1})})}),He(()=>{e.type==="segment"&&de({transitionDisabled:!0})});let _e=0;function Je(t){var a;if(t.contentRect.width===0&&t.contentRect.height===0||_e===t.contentRect.width)return;_e=t.contentRect.width;const{type:s}=e;if((s==="line"||s==="bar")&&Re(),s!=="segment"){const{placement:b}=e;ce((b==="top"||b==="bottom"?(a=$.value)===null||a===void 0?void 0:a.$el:T.value)||null)}}const Qe=he(Je,64);fe([()=>e.justifyContent,()=>e.size],()=>{ue(()=>{const{type:t}=e;(t==="line"||t==="bar")&&Re()})});const q=P(!1);function Ze(t){var a;const{target:s,contentRect:{width:b,height:R}}=t,A=s.parentElement.parentElement.offsetWidth,j=s.parentElement.parentElement.offsetHeight,{placement:Q}=e;if(!q.value)Q==="top"||Q==="bottom"?A<b&&(q.value=!0):j<R&&(q.value=!0);else{const{value:Z}=x;if(!Z)return;Q==="top"||Q==="bottom"?A-b>Z.$el.offsetWidth&&(q.value=!1):j-R>Z.$el.offsetHeight&&(q.value=!1)}ce(((a=$.value)===null||a===void 0?void 0:a.$el)||null)}const et=he(Ze,64);function tt(){const{onAdd:t}=e;t&&t(),ue(()=>{const a=G(),{value:s}=$;!a||!s||s.scrollTo({left:a.offsetLeft,top:0,behavior:"smooth"})})}function ce(t){if(!t)return;const{placement:a}=e;if(a==="top"||a==="bottom"){const{scrollLeft:s,scrollWidth:b,offsetWidth:R}=t;W.value=s<=0,B.value=s+R>=b}else{const{scrollTop:s,scrollHeight:b,offsetHeight:R}=t;W.value=s<=0,B.value=s+R>=b}}const at=he(t=>{ce(t.target)},64);Kt(me,{triggerRef:M(e,"trigger"),tabStyleRef:M(e,"tabStyle"),tabClassRef:M(e,"tabClass"),addTabStyleRef:M(e,"addTabStyle"),addTabClassRef:M(e,"addTabClass"),paneClassRef:M(e,"paneClass"),paneStyleRef:M(e,"paneStyle"),mergedClsPrefixRef:g,typeRef:M(e,"type"),closableRef:M(e,"closable"),valueRef:c,tabChangeIdRef:L,onBeforeLeaveRef:M(e,"onBeforeLeave"),activateTab:Ke,handleClose:qe,handleAdd:tt}),na(()=>{te(),we()}),Mt(()=>{const{value:t}=_;if(!t)return;const{value:a}=g,s=`${a}-tabs-nav-scroll-wrapper--shadow-start`,b=`${a}-tabs-nav-scroll-wrapper--shadow-end`;W.value?t.classList.remove(s):t.classList.add(s),B.value?t.classList.remove(b):t.classList.add(b)});const nt={syncBarPosition:()=>{te()}},rt=()=>{de({transitionDisabled:!0})},$e=V(()=>{const{value:t}=F,{type:a}=e,s={card:"Card",bar:"Bar",line:"Line",segment:"Segment"}[a],b=`${t}${s}`,{self:{barColor:R,closeIconColor:A,closeIconColorHover:j,closeIconColorPressed:Q,tabColor:Z,tabBorderColor:ot,paneTextColor:st,tabFontWeight:it,tabBorderRadius:lt,tabFontWeightActive:dt,colorSegment:ct,fontWeightStrong:bt,tabColorSegment:ft,closeSize:ut,closeIconSize:pt,closeColorHover:vt,closeColorPressed:ht,closeBorderRadius:gt,[H("panePadding",t)]:ne,[H("tabPadding",b)]:xt,[H("tabPaddingVertical",b)]:mt,[H("tabGap",b)]:yt,[H("tabGap",`${b}Vertical`)]:wt,[H("tabTextColor",a)]:Ct,[H("tabTextColorActive",a)]:St,[H("tabTextColorHover",a)]:Rt,[H("tabTextColorDisabled",a)]:_t,[H("tabFontSize",t)]:$t},common:{cubicBezierEaseInOut:Tt}}=v.value;return{"--n-bezier":Tt,"--n-color-segment":ct,"--n-bar-color":R,"--n-tab-font-size":$t,"--n-tab-text-color":Ct,"--n-tab-text-color-active":St,"--n-tab-text-color-disabled":_t,"--n-tab-text-color-hover":Rt,"--n-pane-text-color":st,"--n-tab-border-color":ot,"--n-tab-border-radius":lt,"--n-close-size":ut,"--n-close-icon-size":pt,"--n-close-color-hover":vt,"--n-close-color-pressed":ht,"--n-close-border-radius":gt,"--n-close-icon-color":A,"--n-close-icon-color-hover":j,"--n-close-icon-color-pressed":Q,"--n-tab-color":Z,"--n-tab-font-weight":it,"--n-tab-font-weight-active":dt,"--n-tab-padding":xt,"--n-tab-padding-vertical":mt,"--n-tab-gap":yt,"--n-tab-gap-vertical":wt,"--n-pane-padding-left":re(ne,"left"),"--n-pane-padding-right":re(ne,"right"),"--n-pane-padding-top":re(ne,"top"),"--n-pane-padding-bottom":re(ne,"bottom"),"--n-font-weight-strong":bt,"--n-tab-color-segment":ft}}),J=p?Ft("tabs",V(()=>`${F.value[0]}${e.type[0]}`),$e,e):void 0;return Object.assign({mergedClsPrefix:g,mergedValue:c,renderedNames:new Set,segmentCapsuleElRef:Y,tabsPaneWrapperRef:ae,tabsElRef:h,barElRef:C,addTabInstRef:x,xScrollInstRef:$,scrollWrapperElRef:_,addTabFixed:q,tabWrapperStyle:X,handleNavResize:Qe,mergedSize:F,handleScroll:at,handleTabsResize:et,cssVars:p?void 0:$e,themeClass:J==null?void 0:J.themeClass,animationDirection:Se,renderNameListRef:Ce,yScrollElRef:T,handleSegmentResize:rt,onAnimationBeforeLeave:Ue,onAnimationEnter:Xe,onAnimationAfterEnter:Ge,onRender:J==null?void 0:J.onRender},nt)},render(){const{mergedClsPrefix:e,type:r,placement:o,addTabFixed:u,addable:i,mergedSize:y,renderNameListRef:g,onRender:p,paneWrapperClass:d,paneWrapperStyle:v,$slots:{default:h,prefix:C,suffix:_}}=this;p==null||p();const x=h?pe(h()).filter(w=>w.type.__TAB_PANE__===!0):[],$=h?pe(h()).filter(w=>w.type.__TAB__===!0):[],T=!$.length,W=r==="card",B=r==="segment",k=!W&&!B&&this.justifyContent;g.value=[];const F=()=>{const w=f("div",{style:this.tabWrapperStyle,class:`${e}-tabs-wrapper`},k?null:f("div",{class:`${e}-tabs-scroll-padding`,style:o==="top"||o==="bottom"?{width:`${this.tabsPadding}px`}:{height:`${this.tabsPadding}px`}}),T?x.map((c,L)=>(g.value.push(c.props.name),ge(f(xe,Object.assign({},c.props,{internalCreatedByPane:!0,internalLeftPadded:L!==0&&(!k||k==="center"||k==="start"||k==="end")}),c.children?{default:c.children.tab}:void 0)))):$.map((c,L)=>(g.value.push(c.props.name),ge(L!==0&&!k?Ae(c):c))),!u&&i&&W?Ee(i,(T?x.length:$.length)!==0):null,k?null:f("div",{class:`${e}-tabs-scroll-padding`,style:{width:`${this.tabsPadding}px`}}));return f("div",{ref:"tabsElRef",class:`${e}-tabs-nav-scroll-content`},W&&i?f(be,{onResize:this.handleTabsResize},{default:()=>w}):w,W?f("div",{class:`${e}-tabs-pad`}):null,W?null:f("div",{ref:"barElRef",class:`${e}-tabs-bar`}))},O=B?"top":o;return f("div",{class:[`${e}-tabs`,this.themeClass,`${e}-tabs--${r}-type`,`${e}-tabs--${y}-size`,k&&`${e}-tabs--flex`,`${e}-tabs--${O}`],style:this.cssVars},f("div",{class:[`${e}-tabs-nav--${r}-type`,`${e}-tabs-nav--${O}`,`${e}-tabs-nav`]},ze(C,w=>w&&f("div",{class:`${e}-tabs-nav__prefix`},w)),B?f(be,{onResize:this.handleSegmentResize},{default:()=>f("div",{class:`${e}-tabs-rail`,ref:"tabsElRef"},f("div",{class:`${e}-tabs-capsule`,ref:"segmentCapsuleElRef"},f("div",{class:`${e}-tabs-wrapper`},f("div",{class:`${e}-tabs-tab`}))),T?x.map((w,c)=>(g.value.push(w.props.name),f(xe,Object.assign({},w.props,{internalCreatedByPane:!0,internalLeftPadded:c!==0}),w.children?{default:w.children.tab}:void 0))):$.map((w,c)=>(g.value.push(w.props.name),c===0?w:Ae(w))))}):f(be,{onResize:this.handleNavResize},{default:()=>f("div",{class:`${e}-tabs-nav-scroll-wrapper`,ref:"scrollWrapperElRef"},["top","bottom"].includes(O)?f(sa,{ref:"xScrollInstRef",onScroll:this.handleScroll},{default:F}):f("div",{class:`${e}-tabs-nav-y-scroll`,onScroll:this.handleScroll,ref:"yScrollElRef"},F()))}),u&&i&&W?Ee(i,!0):null,ze(_,w=>w&&f("div",{class:`${e}-tabs-nav__suffix`},w))),T&&(this.animated&&(O==="top"||O==="bottom")?f("div",{ref:"tabsPaneWrapperRef",style:v,class:[`${e}-tabs-pane-wrapper`,d]},Le(x,this.mergedValue,this.renderedNames,this.onAnimationBeforeLeave,this.onAnimationEnter,this.onAnimationAfterEnter,this.animationDirection)):Le(x,this.mergedValue,this.renderedNames)))}});function Le(e,r,o,u,i,y,g){const p=[];return e.forEach(d=>{const{name:v,displayDirective:h,"display-directive":C}=d.props,_=$=>h===$||C===$,x=r===v;if(d.key!==void 0&&(d.key=v),x||_("show")||_("show:lazy")&&o.has(v)){o.has(v)||o.add(v);const $=!_("if");p.push($?Nt(d,[[Gt,x]]):d)}}),g?f(Vt,{name:`${g}-transition`,onBeforeLeave:u,onEnter:i,onAfterEnter:y},{default:()=>p}):p}function Ee(e,r){return f(xe,{ref:"addTabInstRef",key:"__addable",name:"__addable",internalCreatedByPane:!0,internalAddable:!0,internalLeftPadded:r,disabled:typeof e=="object"&&e.disabled})}function Ae(e){const r=Ut(e);return r.props?r.props.internalLeftPadded=!0:r.props={internalLeftPadded:!0},r}function ge(e){return Array.isArray(e.dynamicProps)?e.dynamicProps.includes("internalLeftPadded")||e.dynamicProps.push("internalLeftPadded"):e.dynamicProps=["internalLeftPadded"],e}function Ta(){const{copy:e,copied:r}=Yt(),o=P(!1);async function u(y){await e(y),setTimeout(()=>r.value=!1,2e3)}function i(y,g){const p=new Blob([y],{type:"text/markdown;charset=utf-8"}),d=URL.createObjectURL(p),v=document.createElement("a");v.href=d,v.download=`${g}.md`,v.click(),URL.revokeObjectURL(d)}return{copyContent:u,downloadMarkdown:i,copied:r,downloading:o}}const za={class:"flex items-center justify-between px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]"},ka={class:"flex items-center gap-3"},Pa={class:"text-xl"},Wa={class:"heading-section !mb-0"},Ba={class:"text-xs text-muted mt-0.5"},La={key:0,class:"flex gap-1"},Ea={class:"p-6"},Aa={key:0,class:"prose-content text-sm max-h-[600px] overflow-y-auto"},ja={key:1,class:"flex flex-col items-center py-12 text-dim gap-3"},Ia={key:2,class:"flex flex-col items-center py-12 text-muted gap-2"},Oa=U({__name:"ContentPanel",props:{channel:{},label:{},icon:{},content:{},loading:{type:Boolean}},setup(e){const r=e,{copyContent:o,downloadMarkdown:u,copied:i}=Ta(),y=V(()=>`ribbon-${r.channel}`),g=V(()=>({gongzhonghao:{color:"var(--ch-gongzhonghao)",description:"深度长文 · 专业调性"},zhihu:{color:"var(--ch-zhihu)",description:"知识分享 · 理性洞察"},xiaohongshu:{color:"var(--ch-xiaohongshu)",description:"种草笔记 · 视觉引导"}})[r.channel]??{color:"var(--accent)",description:""});return(p,d)=>{const v=Fe;return E(),I("div",{class:Me(["card !p-0 overflow-hidden animate-enter",y.value])},[m("div",za,[m("div",ka,[m("span",Pa,K(e.icon),1),m("div",null,[m("h3",Wa,K(e.label),1),m("p",Ba,K(g.value.description),1)])]),e.content?(E(),I("div",La,[m("button",{class:"btn-ghost text-xs !px-3 !py-1.5",onClick:d[0]||(d[0]=h=>N(o)(e.content))},K(N(i)?"✓ 已复制":"📋 复制"),1),m("button",{class:"btn-ghost text-xs !px-3 !py-1.5",onClick:d[1]||(d[1]=h=>N(u)(e.content,e.channel))}," 📥 下载 ")])):qt("",!0)]),m("div",Ea,[ee(v,{show:e.loading},{default:ie(()=>[e.content?(E(),I("div",Aa,K(e.content),1)):e.loading?(E(),I("div",ja,[...d[2]||(d[2]=[m("div",{class:"w-12 h-12 skeleton rounded-full"},null,-1),m("div",{class:"w-48 h-3 skeleton"},null,-1)])])):(E(),I("div",Ia,[...d[3]||(d[3]=[m("span",{class:"text-2xl opacity-40"},"📝",-1),m("p",{class:"text-sm"},"等待生成",-1)])]))]),_:1},8,["show"])])],2)}}}),Ha={class:"card !p-0 overflow-hidden ribbon-review animate-enter"},Ma={class:"p-6"},Fa={key:0,class:"prose-content text-sm max-h-[600px] overflow-y-auto"},Da={key:1,class:"flex flex-col items-center py-12 text-dim gap-3"},Na={key:2,class:"flex flex-col items-center py-12 text-muted gap-2"},Va=U({__name:"ReviewReport",props:{report:{},loading:{type:Boolean}},setup(e){return(r,o)=>{const u=Fe;return E(),I("div",Ha,[o[2]||(o[2]=m("div",{class:"flex items-center gap-3 px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]"},[m("span",{class:"text-xl"},"🔍"),m("div",null,[m("h3",{class:"heading-section !mb-0"},"审校报告"),m("p",{class:"text-xs text-muted mt-0.5"},"质量检查 · 一致性校验")])],-1)),m("div",Ma,[ee(u,{show:e.loading},{default:ie(()=>[e.report?(E(),I("div",Fa,K(e.report),1)):e.loading?(E(),I("div",Da,[...o[0]||(o[0]=[m("div",{class:"w-12 h-12 skeleton rounded-full"},null,-1),m("div",{class:"w-48 h-3 skeleton"},null,-1)])])):(E(),I("div",Na,[...o[1]||(o[1]=[m("span",{class:"text-2xl opacity-40"},"✅",-1),m("p",{class:"text-sm"},"等待审校",-1)])]))]),_:1},8,["show"])])])}}}),Ua={class:"h-full overflow-y-auto"},Xa={class:"max-w-3xl mx-auto px-8 py-10 space-y-6"},Ga={class:"flex items-center justify-between animate-enter"},Ka={class:"pt-5"},Qa=U({__name:"Preview",setup(e){const r=Qt(),o=Jt(),u=ta();r.params.projectId;const i=P("gongzhonghao"),y=[{key:"gongzhonghao",label:"公众号",icon:"📰"},{key:"zhihu",label:"知乎",icon:"💡"},{key:"xiaohongshu",label:"小红书",icon:"✨"},{key:"review",label:"审校报告",icon:"🔍"}];He(async()=>{u.connect(),await o.refresh()});function g(v){var h,C,_;return((_=(C=(h=o.status)==null?void 0:h.contents)==null?void 0:C[v])==null?void 0:_.full_content)??null}function p(){var v,h;return((h=(v=o.status)==null?void 0:v.review_report)==null?void 0:h.full_content)??null}const d=V(()=>({generating:{cls:"tag-warning",text:"生成中"},done:{cls:"tag-success",text:"已完成"},review:{cls:"tag-warning",text:"审校中"}})[o.stage]??{cls:"tag-accent",text:"等待中"});return(v,h)=>{const C=Ca,_=$a;return E(),I("div",Ua,[m("div",Xa,[m("div",Ga,[h[1]||(h[1]=m("div",null,[m("h2",{class:"heading-display text-2xl"},"内容预览"),m("p",{class:"text-sm text-dim mt-1"},"三篇内容并行生成 · 审校完成后可导出")],-1)),m("span",{class:Me(N(d).cls)},K(N(d).text),3)]),ee(ra),ee(_,{value:i.value,"onUpdate:value":h[0]||(h[0]=x=>i.value=x),type:"line",animated:"",class:"animate-enter stagger-2"},{default:ie(()=>[(E(),I(Ie,null,Zt(y,x=>ee(C,{key:x.key,name:x.key,tab:`${x.icon} ${x.label}`},{default:ie(()=>[m("div",Ka,[x.key==="review"?(E(),Te(Va,{key:0,report:p(),loading:N(o).stage==="generating"||N(o).stage==="review"},null,8,["report","loading"])):(E(),Te(Oa,{key:1,channel:x.key,label:x.label,icon:x.icon,content:g(x.key),loading:N(o).stage==="generating"&&!g(x.key)},null,8,["channel","label","icon","content","loading"]))])]),_:2},1032,["name","tab"])),64))]),_:1},8,["value"])])])}}});export{Qa as default};
