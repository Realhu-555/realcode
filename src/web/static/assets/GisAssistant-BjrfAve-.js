import{r as T,a as Uo,w as Ie,o as nt,b as Je,c as H,d as ut,i as We,e as tt,f as Ze,u as Ue,g as Qi,h as Ft,F as je,C as ko,j as Se,p as Ge,k as Rr,l as _t,m as ea,n as d,T as ta,t as _e,q as _o,s as En,v as mt,V as ho,x as $o,y as na,z as oa,A as et,B as bt,D as ra,E as ia,G as $n,H as Xn,I as Go,J as aa,K as In,L as Rn,M as la,N as sa,O as zo,P as da,Q as $t,R as Ar,S as Po,U as ca,W as Jt,X as vo,Y as Dr,Z as Xo,_ as ua,$ as Yo,a0 as qo,a1 as _n,a2 as fa,a3 as Zo,a4 as ha,a5 as va,a6 as ga,a7 as pa,a8 as ba,a9 as ma,aa as ya,ab as wa,ac as xa,ad as N,ae as D,af as _,ag as zn,ah as Mo,ai as Zt,aj as To,ak as ot,al as Be,am as Ca,an as at,ao as q,ap as Gt,aq as Qt,ar as en,as as Z,at as De,au as vn,av as An,aw as It,ax as Sa,ay as Ot,az as ka,aA as _a,aB as Bt,aC as $a,aD as Pn,aE as za,aF as Pa,aG as Ma,aH as Lr,aI as Ta,aJ as Fa,aK as Oa,aL as Ba,aM as Wr,aN as Ea,aO as Ia,aP as yn,aQ as Ra,aR as Nr,aS as Aa,aT as Da,aU as La,aV as Wa,aW as Na,aX as se,aY as $,aZ as Nt,a_ as qe,a$ as Vt,b0 as Yn,b1 as Te,b2 as ct,b3 as Va,b4 as Ha,b5 as Mt,b6 as ja,b7 as Ka,b8 as de}from"./index-DQytCjkV.js";import{u as Ua,g as Jo,l as Ga,a as qn,b as Xa,s as Ya,o as Zn,c as qa,d as Za,e as Ja,f as Qa,h as el,i as tl,t as nl,j as ol,_ as rl}from"./_plugin-vue_export-helper-DJpwhsQD.js";let Mn=[];const Vr=new WeakMap;function il(){Mn.forEach(e=>e(...Vr.get(e))),Mn=[]}function Hr(e,...t){Vr.set(e,t),!Mn.includes(e)&&Mn.push(e)===1&&requestAnimationFrame(il)}function cn(e,t){let{target:n}=e;for(;n;){if(n.dataset&&n.dataset[t]!==void 0)return!0;n=n.parentElement}return!1}function al(e){const t=T(!!e.value);if(t.value)return Uo(t);const n=Ie(e,o=>{o&&(t.value=!0,n())});return Uo(t)}const ll=typeof window<"u";let Xt,un;const sl=()=>{var e,t;Xt=ll?(t=(e=document)===null||e===void 0?void 0:e.fonts)===null||t===void 0?void 0:t.ready:void 0,un=!1,Xt!==void 0?Xt.then(()=>{un=!0}):un=!0};sl();function dl(e){if(un)return;let t=!1;nt(()=>{un||Xt==null||Xt.then(()=>{t||e()})}),Je(()=>{t=!0})}function Et(e,t){return Ie(e,n=>{n!==void 0&&(t.value=n)}),H(()=>e.value===void 0?t.value:e.value)}function Fo(e,t){return H(()=>{for(const n of t)if(e[n]!==void 0)return e[n];return e[t[t.length-1]]})}const Oo=ut("n-internal-select-menu"),jr=ut("n-internal-select-menu-body"),Bo=ut("n-drawer-body"),Eo=ut("n-drawer"),Io=ut("n-modal-body"),Ro=ut("n-popover-body"),Kr="__disabled__";function yt(e){const t=We(Io,null),n=We(Bo,null),o=We(Ro,null),r=We(jr,null),a=T();if(typeof document<"u"){a.value=document.fullscreenElement;const l=()=>{a.value=document.fullscreenElement};nt(()=>{tt("fullscreenchange",document,l)}),Je(()=>{Ze("fullscreenchange",document,l)})}return Ue(()=>{var l;const{to:i}=e;return i!==void 0?i===!1?Kr:i===!0?a.value||"body":i:t!=null&&t.value?(l=t.value.$el)!==null&&l!==void 0?l:t.value:n!=null&&n.value?n.value:o!=null&&o.value?o.value:r!=null&&r.value?r.value:i??(a.value||"body")})}yt.tdkey=Kr;yt.propTo={type:[String,Object,Boolean],default:void 0};const gn=typeof document<"u"&&typeof window<"u",Ao=T(!1);function Qo(){Ao.value=!0}function er(){Ao.value=!1}let rn=0;function cl(){return gn&&(Qi(()=>{rn||(window.addEventListener("compositionstart",Qo),window.addEventListener("compositionend",er)),rn++}),Je(()=>{rn<=1?(window.removeEventListener("compositionstart",Qo),window.removeEventListener("compositionend",er),rn=0):rn--})),Ao}let Ht=0,tr="",nr="",or="",rr="";const ir=T("0px");function ul(e){if(typeof document>"u")return;const t=document.documentElement;let n,o=!1;const r=()=>{t.style.marginRight=tr,t.style.overflow=nr,t.style.overflowX=or,t.style.overflowY=rr,ir.value="0px"};nt(()=>{n=Ie(e,a=>{if(a){if(!Ht){const l=window.innerWidth-t.offsetWidth;l>0&&(tr=t.style.marginRight,t.style.marginRight=`${l}px`,ir.value=`${l}px`),nr=t.style.overflow,or=t.style.overflowX,rr=t.style.overflowY,t.style.overflow="hidden",t.style.overflowX="hidden",t.style.overflowY="hidden"}o=!0,Ht++}else Ht--,Ht||r(),o=!1},{immediate:!0})}),Je(()=>{n==null||n(),o&&(Ht--,Ht||r(),o=!1)})}function go(e,t,n="default"){const o=t[n];if(o===void 0)throw new Error(`[vueuc/${e}]: slot[${n}] is empty.`);return o()}function po(e,t=!0,n=[]){return e.forEach(o=>{if(o!==null){if(typeof o!="object"){(typeof o=="string"||typeof o=="number")&&n.push(Ft(String(o)));return}if(Array.isArray(o)){po(o,t,n);return}if(o.type===je){if(o.children===null)return;Array.isArray(o.children)&&po(o.children,t,n)}else o.type!==ko&&n.push(o)}}),n}function ar(e,t,n="default"){const o=t[n];if(o===void 0)throw new Error(`[vueuc/${e}]: slot[${n}] is empty.`);const r=po(o());if(r.length===1)return r[0];throw new Error(`[vueuc/${e}]: slot[${n}] should have exactly one child.`)}let xt=null;function Ur(){if(xt===null&&(xt=document.getElementById("v-binder-view-measurer"),xt===null)){xt=document.createElement("div"),xt.id="v-binder-view-measurer";const{style:e}=xt;e.position="fixed",e.left="0",e.right="0",e.top="0",e.bottom="0",e.pointerEvents="none",e.visibility="hidden",document.body.appendChild(xt)}return xt.getBoundingClientRect()}function fl(e,t){const n=Ur();return{top:t,left:e,height:0,width:0,right:n.width-e,bottom:n.height-t}}function Jn(e){const t=e.getBoundingClientRect(),n=Ur();return{left:t.left-n.left,top:t.top-n.top,bottom:n.height+n.top-t.bottom,right:n.width+n.left-t.right,width:t.width,height:t.height}}function hl(e){return e.nodeType===9?null:e.parentNode}function Gr(e){if(e===null)return null;const t=hl(e);if(t===null)return null;if(t.nodeType===9)return document;if(t.nodeType===1){const{overflow:n,overflowX:o,overflowY:r}=getComputedStyle(t);if(/(auto|scroll|overlay)/.test(n+r+o))return t}return Gr(t)}const Xr=Se({name:"Binder",props:{syncTargetWithParent:Boolean,syncTarget:{type:Boolean,default:!0}},setup(e){var t;Ge("VBinder",(t=Rr())===null||t===void 0?void 0:t.proxy);const n=We("VBinder",null),o=T(null),r=m=>{o.value=m,n&&e.syncTargetWithParent&&n.setTargetRef(m)};let a=[];const l=()=>{let m=o.value;for(;m=Gr(m),m!==null;)a.push(m);for(const B of a)tt("scroll",B,u,!0)},i=()=>{for(const m of a)Ze("scroll",m,u,!0);a=[]},s=new Set,c=m=>{s.size===0&&l(),s.has(m)||s.add(m)},f=m=>{s.has(m)&&s.delete(m),s.size===0&&i()},u=()=>{Hr(p)},p=()=>{s.forEach(m=>m())},y=new Set,h=m=>{y.size===0&&tt("resize",window,w),y.has(m)||y.add(m)},b=m=>{y.has(m)&&y.delete(m),y.size===0&&Ze("resize",window,w)},w=()=>{y.forEach(m=>m())};return Je(()=>{Ze("resize",window,w),i()}),{targetRef:o,setTargetRef:r,addScrollListener:c,removeScrollListener:f,addResizeListener:h,removeResizeListener:b}},render(){return go("binder",this.$slots)}}),Yr=Se({name:"Target",setup(){const{setTargetRef:e,syncTarget:t}=We("VBinder");return{syncTarget:t,setTargetDirective:{mounted:e,updated:e}}},render(){const{syncTarget:e,setTargetDirective:t}=this;return e?_t(ar("follower",this.$slots),[[t]]):ar("follower",this.$slots)}}),jt="@@mmoContext",vl={mounted(e,{value:t}){e[jt]={handler:void 0},typeof t=="function"&&(e[jt].handler=t,tt("mousemoveoutside",e,t))},updated(e,{value:t}){const n=e[jt];typeof t=="function"?n.handler?n.handler!==t&&(Ze("mousemoveoutside",e,n.handler),n.handler=t,tt("mousemoveoutside",e,t)):(e[jt].handler=t,tt("mousemoveoutside",e,t)):n.handler&&(Ze("mousemoveoutside",e,n.handler),n.handler=void 0)},unmounted(e){const{handler:t}=e[jt];t&&Ze("mousemoveoutside",e,t),e[jt].handler=void 0}},Kt="@@coContext",hn={mounted(e,{value:t,modifiers:n}){e[Kt]={handler:void 0},typeof t=="function"&&(e[Kt].handler=t,tt("clickoutside",e,t,{capture:n.capture}))},updated(e,{value:t,modifiers:n}){const o=e[Kt];typeof t=="function"?o.handler?o.handler!==t&&(Ze("clickoutside",e,o.handler,{capture:n.capture}),o.handler=t,tt("clickoutside",e,t,{capture:n.capture})):(e[Kt].handler=t,tt("clickoutside",e,t,{capture:n.capture})):o.handler&&(Ze("clickoutside",e,o.handler,{capture:n.capture}),o.handler=void 0)},unmounted(e,{modifiers:t}){const{handler:n}=e[Kt];n&&Ze("clickoutside",e,n,{capture:t.capture}),e[Kt].handler=void 0}};function gl(e,t){console.error(`[vdirs/${e}]: ${t}`)}class pl{constructor(){this.elementZIndex=new Map,this.nextZIndex=2e3}get elementCount(){return this.elementZIndex.size}ensureZIndex(t,n){const{elementZIndex:o}=this;if(n!==void 0){t.style.zIndex=`${n}`,o.delete(t);return}const{nextZIndex:r}=this;o.has(t)&&o.get(t)+1===this.nextZIndex||(t.style.zIndex=`${r}`,o.set(t,r),this.nextZIndex=r+1,this.squashState())}unregister(t,n){const{elementZIndex:o}=this;o.has(t)?o.delete(t):n===void 0&&gl("z-index-manager/unregister-element","Element not found when unregistering."),this.squashState()}squashState(){const{elementCount:t}=this;t||(this.nextZIndex=2e3),this.nextZIndex-t>2500&&this.rearrange()}rearrange(){const t=Array.from(this.elementZIndex.entries());t.sort((n,o)=>n[1]-o[1]),this.nextZIndex=2e3,t.forEach(n=>{const o=n[0],r=this.nextZIndex++;`${r}`!==o.style.zIndex&&(o.style.zIndex=`${r}`)})}}const Qn=new pl,Ut="@@ziContext",Do={mounted(e,t){const{value:n={}}=t,{zIndex:o,enabled:r}=n;e[Ut]={enabled:!!r,initialized:!1},r&&(Qn.ensureZIndex(e,o),e[Ut].initialized=!0)},updated(e,t){const{value:n={}}=t,{zIndex:o,enabled:r}=n,a=e[Ut].enabled;r&&!a&&(Qn.ensureZIndex(e,o),e[Ut].initialized=!0),e[Ut].enabled=!!r},unmounted(e,t){if(!e[Ut].initialized)return;const{value:n={}}=t,{zIndex:o}=n;Qn.unregister(e,o)}},{c:kt}=ea(),Lo="vueuc-style";function lr(e){return e&-e}class qr{constructor(t,n){this.l=t,this.min=n;const o=new Array(t+1);for(let r=0;r<t+1;++r)o[r]=0;this.ft=o}add(t,n){if(n===0)return;const{l:o,ft:r}=this;for(t+=1;t<=o;)r[t]+=n,t+=lr(t)}get(t){return this.sum(t+1)-this.sum(t)}sum(t){if(t===void 0&&(t=this.l),t<=0)return 0;const{ft:n,min:o,l:r}=this;if(t>r)throw new Error("[FinweckTree.sum]: `i` is larger than length.");let a=t*o;for(;t>0;)a+=n[t],t-=lr(t);return a}getBound(t){let n=0,o=this.l;for(;o>n;){const r=Math.floor((n+o)/2),a=this.sum(r);if(a>t){o=r;continue}else if(a<t){if(n===r)return this.sum(n+1)<=t?n+1:r;n=r}else return r}return n}}function sr(e){return typeof e=="string"?document.querySelector(e):e()||null}const Zr=Se({name:"LazyTeleport",props:{to:{type:[String,Object],default:void 0},disabled:Boolean,show:{type:Boolean,required:!0}},setup(e){return{showTeleport:al(_e(e,"show")),mergedTo:H(()=>{const{to:t}=e;return t??"body"})}},render(){return this.showTeleport?this.disabled?go("lazy-teleport",this.$slots):d(ta,{disabled:this.disabled,to:this.mergedTo},go("lazy-teleport",this.$slots)):null}}),wn={top:"bottom",bottom:"top",left:"right",right:"left"},dr={start:"end",center:"center",end:"start"},eo={top:"height",bottom:"height",left:"width",right:"width"},bl={"bottom-start":"top left",bottom:"top center","bottom-end":"top right","top-start":"bottom left",top:"bottom center","top-end":"bottom right","right-start":"top left",right:"center left","right-end":"bottom left","left-start":"top right",left:"center right","left-end":"bottom right"},ml={"bottom-start":"bottom left",bottom:"bottom center","bottom-end":"bottom right","top-start":"top left",top:"top center","top-end":"top right","right-start":"top right",right:"center right","right-end":"bottom right","left-start":"top left",left:"center left","left-end":"bottom left"},yl={"bottom-start":"right","bottom-end":"left","top-start":"right","top-end":"left","right-start":"bottom","right-end":"top","left-start":"bottom","left-end":"top"},cr={top:!0,bottom:!1,left:!0,right:!1},ur={top:"end",bottom:"start",left:"end",right:"start"};function wl(e,t,n,o,r,a){if(!r||a)return{placement:e,top:0,left:0};const[l,i]=e.split("-");let s=i??"center",c={top:0,left:0};const f=(y,h,b)=>{let w=0,m=0;const B=n[y]-t[h]-t[y];return B>0&&o&&(b?m=cr[h]?B:-B:w=cr[h]?B:-B),{left:w,top:m}},u=l==="left"||l==="right";if(s!=="center"){const y=yl[e],h=wn[y],b=eo[y];if(n[b]>t[b]){if(t[y]+t[b]<n[b]){const w=(n[b]-t[b])/2;t[y]<w||t[h]<w?t[y]<t[h]?(s=dr[i],c=f(b,h,u)):c=f(b,y,u):s="center"}}else n[b]<t[b]&&t[h]<0&&t[y]>t[h]&&(s=dr[i])}else{const y=l==="bottom"||l==="top"?"left":"top",h=wn[y],b=eo[y],w=(n[b]-t[b])/2;(t[y]<w||t[h]<w)&&(t[y]>t[h]?(s=ur[y],c=f(b,y,u)):(s=ur[h],c=f(b,h,u)))}let p=l;return t[l]<n[eo[l]]&&t[l]<t[wn[l]]&&(p=wn[l]),{placement:s!=="center"?`${p}-${s}`:p,left:c.left,top:c.top}}function xl(e,t){return t?ml[e]:bl[e]}function Cl(e,t,n,o,r,a){if(a)switch(e){case"bottom-start":return{top:`${Math.round(n.top-t.top+n.height)}px`,left:`${Math.round(n.left-t.left)}px`,transform:"translateY(-100%)"};case"bottom-end":return{top:`${Math.round(n.top-t.top+n.height)}px`,left:`${Math.round(n.left-t.left+n.width)}px`,transform:"translateX(-100%) translateY(-100%)"};case"top-start":return{top:`${Math.round(n.top-t.top)}px`,left:`${Math.round(n.left-t.left)}px`,transform:""};case"top-end":return{top:`${Math.round(n.top-t.top)}px`,left:`${Math.round(n.left-t.left+n.width)}px`,transform:"translateX(-100%)"};case"right-start":return{top:`${Math.round(n.top-t.top)}px`,left:`${Math.round(n.left-t.left+n.width)}px`,transform:"translateX(-100%)"};case"right-end":return{top:`${Math.round(n.top-t.top+n.height)}px`,left:`${Math.round(n.left-t.left+n.width)}px`,transform:"translateX(-100%) translateY(-100%)"};case"left-start":return{top:`${Math.round(n.top-t.top)}px`,left:`${Math.round(n.left-t.left)}px`,transform:""};case"left-end":return{top:`${Math.round(n.top-t.top+n.height)}px`,left:`${Math.round(n.left-t.left)}px`,transform:"translateY(-100%)"};case"top":return{top:`${Math.round(n.top-t.top)}px`,left:`${Math.round(n.left-t.left+n.width/2)}px`,transform:"translateX(-50%)"};case"right":return{top:`${Math.round(n.top-t.top+n.height/2)}px`,left:`${Math.round(n.left-t.left+n.width)}px`,transform:"translateX(-100%) translateY(-50%)"};case"left":return{top:`${Math.round(n.top-t.top+n.height/2)}px`,left:`${Math.round(n.left-t.left)}px`,transform:"translateY(-50%)"};case"bottom":default:return{top:`${Math.round(n.top-t.top+n.height)}px`,left:`${Math.round(n.left-t.left+n.width/2)}px`,transform:"translateX(-50%) translateY(-100%)"}}switch(e){case"bottom-start":return{top:`${Math.round(n.top-t.top+n.height+o)}px`,left:`${Math.round(n.left-t.left+r)}px`,transform:""};case"bottom-end":return{top:`${Math.round(n.top-t.top+n.height+o)}px`,left:`${Math.round(n.left-t.left+n.width+r)}px`,transform:"translateX(-100%)"};case"top-start":return{top:`${Math.round(n.top-t.top+o)}px`,left:`${Math.round(n.left-t.left+r)}px`,transform:"translateY(-100%)"};case"top-end":return{top:`${Math.round(n.top-t.top+o)}px`,left:`${Math.round(n.left-t.left+n.width+r)}px`,transform:"translateX(-100%) translateY(-100%)"};case"right-start":return{top:`${Math.round(n.top-t.top+o)}px`,left:`${Math.round(n.left-t.left+n.width+r)}px`,transform:""};case"right-end":return{top:`${Math.round(n.top-t.top+n.height+o)}px`,left:`${Math.round(n.left-t.left+n.width+r)}px`,transform:"translateY(-100%)"};case"left-start":return{top:`${Math.round(n.top-t.top+o)}px`,left:`${Math.round(n.left-t.left+r)}px`,transform:"translateX(-100%)"};case"left-end":return{top:`${Math.round(n.top-t.top+n.height+o)}px`,left:`${Math.round(n.left-t.left+r)}px`,transform:"translateX(-100%) translateY(-100%)"};case"top":return{top:`${Math.round(n.top-t.top+o)}px`,left:`${Math.round(n.left-t.left+n.width/2+r)}px`,transform:"translateY(-100%) translateX(-50%)"};case"right":return{top:`${Math.round(n.top-t.top+n.height/2+o)}px`,left:`${Math.round(n.left-t.left+n.width+r)}px`,transform:"translateY(-50%)"};case"left":return{top:`${Math.round(n.top-t.top+n.height/2+o)}px`,left:`${Math.round(n.left-t.left+r)}px`,transform:"translateY(-50%) translateX(-100%)"};case"bottom":default:return{top:`${Math.round(n.top-t.top+n.height+o)}px`,left:`${Math.round(n.left-t.left+n.width/2+r)}px`,transform:"translateX(-50%)"}}}const Sl=kt([kt(".v-binder-follower-container",{position:"absolute",left:"0",right:"0",top:"0",height:"0",pointerEvents:"none",zIndex:"auto"}),kt(".v-binder-follower-content",{position:"absolute",zIndex:"auto"},[kt("> *",{pointerEvents:"all"})])]),Jr=Se({name:"Follower",inheritAttrs:!1,props:{show:Boolean,enabled:{type:Boolean,default:void 0},placement:{type:String,default:"bottom"},syncTrigger:{type:Array,default:["resize","scroll"]},to:[String,Object],flip:{type:Boolean,default:!0},internalShift:Boolean,x:Number,y:Number,width:String,minWidth:String,containerClass:String,teleportDisabled:Boolean,zindexable:{type:Boolean,default:!0},zIndex:Number,overlap:Boolean},setup(e){const t=We("VBinder"),n=Ue(()=>e.enabled!==void 0?e.enabled:e.show),o=T(null),r=T(null),a=()=>{const{syncTrigger:p}=e;p.includes("scroll")&&t.addScrollListener(s),p.includes("resize")&&t.addResizeListener(s)},l=()=>{t.removeScrollListener(s),t.removeResizeListener(s)};nt(()=>{n.value&&(s(),a())});const i=_o();Sl.mount({id:"vueuc/binder",head:!0,anchorMetaName:Lo,ssr:i}),Je(()=>{l()}),dl(()=>{n.value&&s()});const s=()=>{if(!n.value)return;const p=o.value;if(p===null)return;const y=t.targetRef,{x:h,y:b,overlap:w}=e,m=h!==void 0&&b!==void 0?fl(h,b):Jn(y);p.style.setProperty("--v-target-width",`${Math.round(m.width)}px`),p.style.setProperty("--v-target-height",`${Math.round(m.height)}px`);const{width:B,minWidth:W,placement:F,internalShift:C,flip:P}=e;p.setAttribute("v-placement",F),w?p.setAttribute("v-overlap",""):p.removeAttribute("v-overlap");const{style:V}=p;B==="target"?V.width=`${m.width}px`:B!==void 0?V.width=B:V.width="",W==="target"?V.minWidth=`${m.width}px`:W!==void 0?V.minWidth=W:V.minWidth="";const S=Jn(p),k=Jn(r.value),{left:R,top:K,placement:j}=wl(F,m,S,C,P,w),z=xl(j,w),{left:G,top:E,transform:J}=Cl(j,k,m,K,R,w);p.setAttribute("v-placement",j),p.style.setProperty("--v-offset-left",`${Math.round(R)}px`),p.style.setProperty("--v-offset-top",`${Math.round(K)}px`),p.style.transform=`translateX(${G}) translateY(${E}) ${J}`,p.style.setProperty("--v-transform-origin",z),p.style.transformOrigin=z};Ie(n,p=>{p?(a(),c()):l()});const c=()=>{mt().then(s).catch(p=>console.error(p))};["placement","x","y","internalShift","flip","width","overlap","minWidth"].forEach(p=>{Ie(_e(e,p),s)}),["teleportDisabled"].forEach(p=>{Ie(_e(e,p),c)}),Ie(_e(e,"syncTrigger"),p=>{p.includes("resize")?t.addResizeListener(s):t.removeResizeListener(s),p.includes("scroll")?t.addScrollListener(s):t.removeScrollListener(s)});const f=En(),u=Ue(()=>{const{to:p}=e;if(p!==void 0)return p;f.value});return{VBinder:t,mergedEnabled:n,offsetContainerRef:r,followerRef:o,mergedTo:u,syncPosition:s}},render(){return d(Zr,{show:this.show,to:this.mergedTo,disabled:this.teleportDisabled},{default:()=>{var e,t;const n=d("div",{class:["v-binder-follower-container",this.containerClass],ref:"offsetContainerRef"},[d("div",{class:"v-binder-follower-content",ref:"followerRef"},(t=(e=this.$slots).default)===null||t===void 0?void 0:t.call(e))]);return this.zindexable?_t(n,[[Do,{enabled:this.mergedEnabled,zIndex:this.zIndex}]]):n}})}});let xn;function kl(){return typeof document>"u"?!1:(xn===void 0&&("matchMedia"in window?xn=window.matchMedia("(pointer:coarse)").matches:xn=!1),xn)}let to;function fr(){return typeof document>"u"?1:(to===void 0&&(to="chrome"in window?window.devicePixelRatio:1),to)}const Qr="VVirtualListXScroll";function _l({columnsRef:e,renderColRef:t,renderItemWithColsRef:n}){const o=T(0),r=T(0),a=H(()=>{const c=e.value;if(c.length===0)return null;const f=new qr(c.length,0);return c.forEach((u,p)=>{f.add(p,u.width)}),f}),l=Ue(()=>{const c=a.value;return c!==null?Math.max(c.getBound(r.value)-1,0):0}),i=c=>{const f=a.value;return f!==null?f.sum(c):0},s=Ue(()=>{const c=a.value;return c!==null?Math.min(c.getBound(r.value+o.value)+1,e.value.length-1):0});return Ge(Qr,{startIndexRef:l,endIndexRef:s,columnsRef:e,renderColRef:t,renderItemWithColsRef:n,getLeft:i}),{listWidthRef:o,scrollLeftRef:r}}const hr=Se({name:"VirtualListRow",props:{index:{type:Number,required:!0},item:{type:Object,required:!0}},setup(){const{startIndexRef:e,endIndexRef:t,columnsRef:n,getLeft:o,renderColRef:r,renderItemWithColsRef:a}=We(Qr);return{startIndex:e,endIndex:t,columns:n,renderCol:r,renderItemWithCols:a,getLeft:o}},render(){const{startIndex:e,endIndex:t,columns:n,renderCol:o,renderItemWithCols:r,getLeft:a,item:l}=this;if(r!=null)return r({itemIndex:this.index,startColIndex:e,endColIndex:t,allColumns:n,item:l,getLeft:a});if(o!=null){const i=[];for(let s=e;s<=t;++s){const c=n[s];i.push(o({column:c,left:a(s),item:l}))}return i}return null}}),$l=kt(".v-vl",{maxHeight:"inherit",height:"100%",overflow:"auto",minWidth:"1px"},[kt("&:not(.v-vl--show-scrollbar)",{scrollbarWidth:"none"},[kt("&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb",{width:0,height:0,display:"none"})])]),zl=Se({name:"VirtualList",inheritAttrs:!1,props:{showScrollbar:{type:Boolean,default:!0},columns:{type:Array,default:()=>[]},renderCol:Function,renderItemWithCols:Function,items:{type:Array,default:()=>[]},itemSize:{type:Number,required:!0},itemResizable:Boolean,itemsStyle:[String,Object],visibleItemsTag:{type:[String,Object],default:"div"},visibleItemsProps:Object,ignoreItemResize:Boolean,onScroll:Function,onWheel:Function,onResize:Function,defaultScrollKey:[Number,String],defaultScrollIndex:Number,keyField:{type:String,default:"key"},paddingTop:{type:[Number,String],default:0},paddingBottom:{type:[Number,String],default:0}},setup(e){const t=_o();$l.mount({id:"vueuc/virtual-list",head:!0,anchorMetaName:Lo,ssr:t}),nt(()=>{const{defaultScrollIndex:z,defaultScrollKey:G}=e;z!=null?w({index:z}):G!=null&&w({key:G})});let n=!1,o=!1;na(()=>{if(n=!1,!o){o=!0;return}w({top:y.value,left:l.value})}),oa(()=>{n=!0,o||(o=!0)});const r=Ue(()=>{if(e.renderCol==null&&e.renderItemWithCols==null||e.columns.length===0)return;let z=0;return e.columns.forEach(G=>{z+=G.width}),z}),a=H(()=>{const z=new Map,{keyField:G}=e;return e.items.forEach((E,J)=>{z.set(E[G],J)}),z}),{scrollLeftRef:l,listWidthRef:i}=_l({columnsRef:_e(e,"columns"),renderColRef:_e(e,"renderCol"),renderItemWithColsRef:_e(e,"renderItemWithCols")}),s=T(null),c=T(void 0),f=new Map,u=H(()=>{const{items:z,itemSize:G,keyField:E}=e,J=new qr(z.length,G);return z.forEach((Q,X)=>{const te=Q[E],ue=f.get(te);ue!==void 0&&J.add(X,ue)}),J}),p=T(0),y=T(0),h=Ue(()=>Math.max(u.value.getBound(y.value-et(e.paddingTop))-1,0)),b=H(()=>{const{value:z}=c;if(z===void 0)return[];const{items:G,itemSize:E}=e,J=h.value,Q=Math.min(J+Math.ceil(z/E+1),G.length-1),X=[];for(let te=J;te<=Q;++te)X.push(G[te]);return X}),w=(z,G)=>{if(typeof z=="number"){F(z,G,"auto");return}const{left:E,top:J,index:Q,key:X,position:te,behavior:ue,debounce:le=!0}=z;if(E!==void 0||J!==void 0)F(E,J,ue);else if(Q!==void 0)W(Q,ue,le);else if(X!==void 0){const re=a.value.get(X);re!==void 0&&W(re,ue,le)}else te==="bottom"?F(0,Number.MAX_SAFE_INTEGER,ue):te==="top"&&F(0,0,ue)};let m,B=null;function W(z,G,E){const{value:J}=u,Q=J.sum(z)+et(e.paddingTop);if(!E)s.value.scrollTo({left:0,top:Q,behavior:G});else{m=z,B!==null&&window.clearTimeout(B),B=window.setTimeout(()=>{m=void 0,B=null},16);const{scrollTop:X,offsetHeight:te}=s.value;if(Q>X){const ue=J.get(z);Q+ue<=X+te||s.value.scrollTo({left:0,top:Q+ue-te,behavior:G})}else s.value.scrollTo({left:0,top:Q,behavior:G})}}function F(z,G,E){s.value.scrollTo({left:z,top:G,behavior:E})}function C(z,G){var E,J,Q;if(n||e.ignoreItemResize||j(G.target))return;const{value:X}=u,te=a.value.get(z),ue=X.get(te),le=(Q=(J=(E=G.borderBoxSize)===null||E===void 0?void 0:E[0])===null||J===void 0?void 0:J.blockSize)!==null&&Q!==void 0?Q:G.contentRect.height;if(le===ue)return;le-e.itemSize===0?f.delete(z):f.set(z,le-e.itemSize);const xe=le-ue;if(xe===0)return;X.add(te,xe);const O=s.value;if(O!=null){if(m===void 0){const L=X.sum(te);O.scrollTop>L&&O.scrollBy(0,xe)}else if(te<m)O.scrollBy(0,xe);else if(te===m){const L=X.sum(te);le+L>O.scrollTop+O.offsetHeight&&O.scrollBy(0,xe)}K()}p.value++}const P=!kl();let V=!1;function S(z){var G;(G=e.onScroll)===null||G===void 0||G.call(e,z),(!P||!V)&&K()}function k(z){var G;if((G=e.onWheel)===null||G===void 0||G.call(e,z),P){const E=s.value;if(E!=null){if(z.deltaX===0&&(E.scrollTop===0&&z.deltaY<=0||E.scrollTop+E.offsetHeight>=E.scrollHeight&&z.deltaY>=0))return;z.preventDefault(),E.scrollTop+=z.deltaY/fr(),E.scrollLeft+=z.deltaX/fr(),K(),V=!0,Hr(()=>{V=!1})}}}function R(z){if(n||j(z.target))return;if(e.renderCol==null&&e.renderItemWithCols==null){if(z.contentRect.height===c.value)return}else if(z.contentRect.height===c.value&&z.contentRect.width===i.value)return;c.value=z.contentRect.height,i.value=z.contentRect.width;const{onResize:G}=e;G!==void 0&&G(z)}function K(){const{value:z}=s;z!=null&&(y.value=z.scrollTop,l.value=z.scrollLeft)}function j(z){let G=z;for(;G!==null;){if(G.style.display==="none")return!0;G=G.parentElement}return!1}return{listHeight:c,listStyle:{overflow:"auto"},keyToIndex:a,itemsStyle:H(()=>{const{itemResizable:z}=e,G=bt(u.value.sum());return p.value,[e.itemsStyle,{boxSizing:"content-box",width:bt(r.value),height:z?"":G,minHeight:z?G:"",paddingTop:bt(e.paddingTop),paddingBottom:bt(e.paddingBottom)}]}),visibleItemsStyle:H(()=>(p.value,{transform:`translateY(${bt(u.value.sum(h.value))})`})),viewportItems:b,listElRef:s,itemsElRef:T(null),scrollTo:w,handleListResize:R,handleListScroll:S,handleListWheel:k,handleItemResize:C}},render(){const{itemResizable:e,keyField:t,keyToIndex:n,visibleItemsTag:o}=this;return d(ho,{onResize:this.handleListResize},{default:()=>{var r,a;return d("div",$o(this.$attrs,{class:["v-vl",this.showScrollbar&&"v-vl--show-scrollbar"],onScroll:this.handleListScroll,onWheel:this.handleListWheel,ref:"listElRef"}),[this.items.length!==0?d("div",{ref:"itemsElRef",class:"v-vl-items",style:this.itemsStyle},[d(o,Object.assign({class:"v-vl-visible-items",style:this.visibleItemsStyle},this.visibleItemsProps),{default:()=>{const{renderCol:l,renderItemWithCols:i}=this;return this.viewportItems.map(s=>{const c=s[t],f=n.get(c),u=l!=null?d(hr,{index:f,item:s}):void 0,p=i!=null?d(hr,{index:f,item:s}):void 0,y=this.$slots.default({item:s,renderedCols:u,renderedItemWithCols:p,index:f})[0];return e?d(ho,{key:c,onResize:h=>this.handleItemResize(c,h)},{default:()=>y}):(y.key=c,y)})}})]):(a=(r=this.$slots).empty)===null||a===void 0?void 0:a.call(r)])}})}}),gt="v-hidden",Pl=kt("[v-hidden]",{display:"none!important"}),vr=Se({name:"Overflow",props:{getCounter:Function,getTail:Function,updateCounter:Function,onUpdateCount:Function,onUpdateOverflow:Function},setup(e,{slots:t}){const n=T(null),o=T(null);function r(l){const{value:i}=n,{getCounter:s,getTail:c}=e;let f;if(s!==void 0?f=s():f=o.value,!i||!f)return;f.hasAttribute(gt)&&f.removeAttribute(gt);const{children:u}=i;if(l.showAllItemsBeforeCalculate)for(const W of u)W.hasAttribute(gt)&&W.removeAttribute(gt);const p=i.offsetWidth,y=[],h=t.tail?c==null?void 0:c():null;let b=h?h.offsetWidth:0,w=!1;const m=i.children.length-(t.tail?1:0);for(let W=0;W<m-1;++W){if(W<0)continue;const F=u[W];if(w){F.hasAttribute(gt)||F.setAttribute(gt,"");continue}else F.hasAttribute(gt)&&F.removeAttribute(gt);const C=F.offsetWidth;if(b+=C,y[W]=C,b>p){const{updateCounter:P}=e;for(let V=W;V>=0;--V){const S=m-1-V;P!==void 0?P(S):f.textContent=`${S}`;const k=f.offsetWidth;if(b-=y[V],b+k<=p||V===0){w=!0,W=V-1,h&&(W===-1?(h.style.maxWidth=`${p-k}px`,h.style.boxSizing="border-box"):h.style.maxWidth="");const{onUpdateCount:R}=e;R&&R(S);break}}}}const{onUpdateOverflow:B}=e;w?B!==void 0&&B(!0):(B!==void 0&&B(!1),f.setAttribute(gt,""))}const a=_o();return Pl.mount({id:"vueuc/overflow",head:!0,anchorMetaName:Lo,ssr:a}),nt(()=>r({showAllItemsBeforeCalculate:!1})),{selfRef:n,counterRef:o,sync:r}},render(){const{$slots:e}=this;return mt(()=>this.sync({showAllItemsBeforeCalculate:!1})),d("div",{class:"v-overflow",ref:"selfRef"},[ra(e,"default"),e.counter?e.counter():d("span",{style:{display:"inline-block"},ref:"counterRef"}),e.tail?e.tail():null])}});function ei(e){return e instanceof HTMLElement}function ti(e){for(let t=0;t<e.childNodes.length;t++){const n=e.childNodes[t];if(ei(n)&&(oi(n)||ti(n)))return!0}return!1}function ni(e){for(let t=e.childNodes.length-1;t>=0;t--){const n=e.childNodes[t];if(ei(n)&&(oi(n)||ni(n)))return!0}return!1}function oi(e){if(!Ml(e))return!1;try{e.focus({preventScroll:!0})}catch{}return document.activeElement===e}function Ml(e){if(e.tabIndex>0||e.tabIndex===0&&e.getAttribute("tabIndex")!==null)return!0;if(e.getAttribute("disabled"))return!1;switch(e.nodeName){case"A":return!!e.href&&e.rel!=="ignore";case"INPUT":return e.type!=="hidden"&&e.type!=="file";case"SELECT":case"TEXTAREA":return!0;default:return!1}}let an=[];const ri=Se({name:"FocusTrap",props:{disabled:Boolean,active:Boolean,autoFocus:{type:Boolean,default:!0},onEsc:Function,initialFocusTo:[String,Function],finalFocusTo:[String,Function],returnFocusOnDeactivated:{type:Boolean,default:!0}},setup(e){const t=ia(),n=T(null),o=T(null);let r=!1,a=!1;const l=typeof document>"u"?null:document.activeElement;function i(){return an[an.length-1]===t}function s(w){var m;w.code==="Escape"&&i()&&((m=e.onEsc)===null||m===void 0||m.call(e,w))}nt(()=>{Ie(()=>e.active,w=>{w?(u(),tt("keydown",document,s)):(Ze("keydown",document,s),r&&p())},{immediate:!0})}),Je(()=>{Ze("keydown",document,s),r&&p()});function c(w){if(!a&&i()){const m=f();if(m===null||m.contains($n(w)))return;y("first")}}function f(){const w=n.value;if(w===null)return null;let m=w;for(;m=m.nextSibling,!(m===null||m instanceof Element&&m.tagName==="DIV"););return m}function u(){var w;if(!e.disabled){if(an.push(t),e.autoFocus){const{initialFocusTo:m}=e;m===void 0?y("first"):(w=sr(m))===null||w===void 0||w.focus({preventScroll:!0})}r=!0,document.addEventListener("focus",c,!0)}}function p(){var w;if(e.disabled||(document.removeEventListener("focus",c,!0),an=an.filter(B=>B!==t),i()))return;const{finalFocusTo:m}=e;m!==void 0?(w=sr(m))===null||w===void 0||w.focus({preventScroll:!0}):e.returnFocusOnDeactivated&&l instanceof HTMLElement&&(a=!0,l.focus({preventScroll:!0}),a=!1)}function y(w){if(i()&&e.active){const m=n.value,B=o.value;if(m!==null&&B!==null){const W=f();if(W==null||W===B){a=!0,m.focus({preventScroll:!0}),a=!1;return}a=!0;const F=w==="first"?ti(W):ni(W);a=!1,F||(a=!0,m.focus({preventScroll:!0}),a=!1)}}}function h(w){if(a)return;const m=f();m!==null&&(w.relatedTarget!==null&&m.contains(w.relatedTarget)?y("last"):y("first"))}function b(w){a||(w.relatedTarget!==null&&w.relatedTarget===n.value?y("last"):y("first"))}return{focusableStartRef:n,focusableEndRef:o,focusableStyle:"position: absolute; height: 0; width: 0;",handleStartFocus:h,handleEndFocus:b}},render(){const{default:e}=this.$slots;if(e===void 0)return null;if(this.disabled)return e();const{active:t,focusableStyle:n}=this;return d(je,null,[d("div",{"aria-hidden":"true",tabindex:t?"0":"-1",ref:"focusableStartRef",style:n,onFocus:this.handleStartFocus}),e(),d("div",{"aria-hidden":"true",style:n,ref:"focusableEndRef",tabindex:t?"0":"-1",onFocus:this.handleEndFocus})])}});function ii(e,t){t&&(nt(()=>{const{value:n}=e;n&&Xn.registerHandler(n,t)}),Ie(e,(n,o)=>{o&&Xn.unregisterHandler(o)},{deep:!1}),Je(()=>{const{value:n}=e;n&&Xn.unregisterHandler(n)}))}function Tn(e){return e.replace(/#|\(|\)|,|\s|\./g,"_")}const Tl=/^(\d|\.)+$/,gr=/(\d|\.)+/;function fn(e,{c:t=1,offset:n=0,attachPx:o=!0}={}){if(typeof e=="number"){const r=(e+n)*t;return r===0?"0":`${r}px`}else if(typeof e=="string")if(Tl.test(e)){const r=(Number(e)+n)*t;return o?r===0?"0":`${r}px`:`${r}`}else{const r=gr.exec(e);return r?e.replace(gr,String((Number(r[0])+n)*t)):e}return e}let no;function Fl(){return no===void 0&&(no=navigator.userAgent.includes("Node.js")||navigator.userAgent.includes("jsdom")),no}const ai=new WeakSet;function Ol(e){ai.add(e)}function Bl(e){return!ai.has(e)}function pr(e){switch(typeof e){case"string":return e||void 0;case"number":return String(e);default:return}}function ge(e,...t){if(Array.isArray(e))e.forEach(n=>ge(n,...t));else return e(...t)}function bo(e,t=!0,n=[]){return e.forEach(o=>{if(o!==null){if(typeof o!="object"){(typeof o=="string"||typeof o=="number")&&n.push(Ft(String(o)));return}if(Array.isArray(o)){bo(o,t,n);return}if(o.type===je){if(o.children===null)return;Array.isArray(o.children)&&bo(o.children,t,n)}else{if(o.type===ko&&t)return;n.push(o)}}}),n}function El(e,t="default",n=void 0){const o=e[t];if(!o)return Go("getFirstSlotVNode",`slot[${t}] is empty`),null;const r=bo(o(n));return r.length===1?r[0]:(Go("getFirstSlotVNode",`slot[${t}] should have exactly one child`),null)}function oo(e){const t=e.filter(n=>n!==void 0);if(t.length!==0)return t.length===1?t[0]:n=>{e.forEach(o=>{o&&o(n)})}}function pn(e){return e.some(t=>aa(t)?!(t.type===ko||t.type===je&&!pn(t.children)):!0)?e:null}function Yt(e,t){return e&&pn(e())||t()}function Il(e,t,n){return e&&pn(e(t))||n(t)}function Re(e,t){const n=e&&pn(e());return t(n||null)}function qt(e){return!(e&&pn(e()))}const br=ut("n-form-item");function Dn(e,{defaultSize:t="medium",mergedSize:n,mergedDisabled:o}={}){const r=We(br,null);Ge(br,null);const a=H(n?()=>n(r):()=>{const{size:s}=e;if(s)return s;if(r){const{mergedSize:c}=r;if(c.value!==void 0)return c.value}return t}),l=H(o?()=>o(r):()=>{const{disabled:s}=e;return s!==void 0?s:r?r.disabled.value:!1}),i=H(()=>{const{status:s}=e;return s||(r==null?void 0:r.mergedValidationStatus.value)});return Je(()=>{r&&r.restoreValidation()}),{mergedSizeRef:a,mergedDisabledRef:l,mergedStatusRef:i,nTriggerFormBlur(){r&&r.handleContentBlur()},nTriggerFormChange(){r&&r.handleContentChange()},nTriggerFormFocus(){r&&r.handleContentFocus()},nTriggerFormInput(){r&&r.handleContentInput()}}}const Rl={name:"en-US",global:{undo:"Undo",redo:"Redo",confirm:"Confirm",clear:"Clear"},Popconfirm:{positiveText:"Confirm",negativeText:"Cancel"},Cascader:{placeholder:"Please Select",loading:"Loading",loadingRequiredMessage:e=>`Please load all ${e}'s descendants before checking it.`},Time:{dateFormat:"yyyy-MM-dd",dateTimeFormat:"yyyy-MM-dd HH:mm:ss"},DatePicker:{yearFormat:"yyyy",monthFormat:"MMM",dayFormat:"eeeeee",yearTypeFormat:"yyyy",monthTypeFormat:"yyyy-MM",dateFormat:"yyyy-MM-dd",dateTimeFormat:"yyyy-MM-dd HH:mm:ss",quarterFormat:"yyyy-qqq",weekFormat:"YYYY-w",clear:"Clear",now:"Now",confirm:"Confirm",selectTime:"Select Time",selectDate:"Select Date",datePlaceholder:"Select Date",datetimePlaceholder:"Select Date and Time",monthPlaceholder:"Select Month",yearPlaceholder:"Select Year",quarterPlaceholder:"Select Quarter",weekPlaceholder:"Select Week",startDatePlaceholder:"Start Date",endDatePlaceholder:"End Date",startDatetimePlaceholder:"Start Date and Time",endDatetimePlaceholder:"End Date and Time",startMonthPlaceholder:"Start Month",endMonthPlaceholder:"End Month",monthBeforeYear:!0,firstDayOfWeek:6,today:"Today"},DataTable:{checkTableAll:"Select all in the table",uncheckTableAll:"Unselect all in the table",confirm:"Confirm",clear:"Clear"},LegacyTransfer:{sourceTitle:"Source",targetTitle:"Target"},Transfer:{selectAll:"Select all",unselectAll:"Unselect all",clearAll:"Clear",total:e=>`Total ${e} items`,selected:e=>`${e} items selected`},Empty:{description:"No Data"},Select:{placeholder:"Please Select"},TimePicker:{placeholder:"Select Time",positiveText:"OK",negativeText:"Cancel",now:"Now",clear:"Clear"},Pagination:{goto:"Goto",selectionSuffix:"page"},DynamicTags:{add:"Add"},Log:{loading:"Loading"},Input:{placeholder:"Please Input"},InputNumber:{placeholder:"Please Input"},DynamicInput:{create:"Create"},ThemeEditor:{title:"Theme Editor",clearAllVars:"Clear All Variables",clearSearch:"Clear Search",filterCompName:"Filter Component Name",filterVarName:"Filter Variable Name",import:"Import",export:"Export",restore:"Reset to Default"},Image:{tipPrevious:"Previous picture (←)",tipNext:"Next picture (→)",tipCounterclockwise:"Counterclockwise",tipClockwise:"Clockwise",tipZoomOut:"Zoom out",tipZoomIn:"Zoom in",tipDownload:"Download",tipClose:"Close (Esc)",tipOriginalSize:"Zoom to original size"},Heatmap:{less:"less",more:"more",monthFormat:"MMM",weekdayFormat:"eee"}};function ro(e){return(t={})=>{const n=t.width?String(t.width):e.defaultWidth;return e.formats[n]||e.formats[e.defaultWidth]}}function ln(e){return(t,n)=>{const o=n!=null&&n.context?String(n.context):"standalone";let r;if(o==="formatting"&&e.formattingValues){const l=e.defaultFormattingWidth||e.defaultWidth,i=n!=null&&n.width?String(n.width):l;r=e.formattingValues[i]||e.formattingValues[l]}else{const l=e.defaultWidth,i=n!=null&&n.width?String(n.width):e.defaultWidth;r=e.values[i]||e.values[l]}const a=e.argumentCallback?e.argumentCallback(t):t;return r[a]}}function sn(e){return(t,n={})=>{const o=n.width,r=o&&e.matchPatterns[o]||e.matchPatterns[e.defaultMatchWidth],a=t.match(r);if(!a)return null;const l=a[0],i=o&&e.parsePatterns[o]||e.parsePatterns[e.defaultParseWidth],s=Array.isArray(i)?Dl(i,u=>u.test(l)):Al(i,u=>u.test(l));let c;c=e.valueCallback?e.valueCallback(s):s,c=n.valueCallback?n.valueCallback(c):c;const f=t.slice(l.length);return{value:c,rest:f}}}function Al(e,t){for(const n in e)if(Object.prototype.hasOwnProperty.call(e,n)&&t(e[n]))return n}function Dl(e,t){for(let n=0;n<e.length;n++)if(t(e[n]))return n}function Ll(e){return(t,n={})=>{const o=t.match(e.matchPattern);if(!o)return null;const r=o[0],a=t.match(e.parsePattern);if(!a)return null;let l=e.valueCallback?e.valueCallback(a[0]):a[0];l=n.valueCallback?n.valueCallback(l):l;const i=t.slice(r.length);return{value:l,rest:i}}}const Wl={lessThanXSeconds:{one:"less than a second",other:"less than {{count}} seconds"},xSeconds:{one:"1 second",other:"{{count}} seconds"},halfAMinute:"half a minute",lessThanXMinutes:{one:"less than a minute",other:"less than {{count}} minutes"},xMinutes:{one:"1 minute",other:"{{count}} minutes"},aboutXHours:{one:"about 1 hour",other:"about {{count}} hours"},xHours:{one:"1 hour",other:"{{count}} hours"},xDays:{one:"1 day",other:"{{count}} days"},aboutXWeeks:{one:"about 1 week",other:"about {{count}} weeks"},xWeeks:{one:"1 week",other:"{{count}} weeks"},aboutXMonths:{one:"about 1 month",other:"about {{count}} months"},xMonths:{one:"1 month",other:"{{count}} months"},aboutXYears:{one:"about 1 year",other:"about {{count}} years"},xYears:{one:"1 year",other:"{{count}} years"},overXYears:{one:"over 1 year",other:"over {{count}} years"},almostXYears:{one:"almost 1 year",other:"almost {{count}} years"}},Nl=(e,t,n)=>{let o;const r=Wl[e];return typeof r=="string"?o=r:t===1?o=r.one:o=r.other.replace("{{count}}",t.toString()),n!=null&&n.addSuffix?n.comparison&&n.comparison>0?"in "+o:o+" ago":o},Vl={lastWeek:"'last' eeee 'at' p",yesterday:"'yesterday at' p",today:"'today at' p",tomorrow:"'tomorrow at' p",nextWeek:"eeee 'at' p",other:"P"},Hl=(e,t,n,o)=>Vl[e],jl={narrow:["B","A"],abbreviated:["BC","AD"],wide:["Before Christ","Anno Domini"]},Kl={narrow:["1","2","3","4"],abbreviated:["Q1","Q2","Q3","Q4"],wide:["1st quarter","2nd quarter","3rd quarter","4th quarter"]},Ul={narrow:["J","F","M","A","M","J","J","A","S","O","N","D"],abbreviated:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],wide:["January","February","March","April","May","June","July","August","September","October","November","December"]},Gl={narrow:["S","M","T","W","T","F","S"],short:["Su","Mo","Tu","We","Th","Fr","Sa"],abbreviated:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],wide:["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]},Xl={narrow:{am:"a",pm:"p",midnight:"mi",noon:"n",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"},abbreviated:{am:"AM",pm:"PM",midnight:"midnight",noon:"noon",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"},wide:{am:"a.m.",pm:"p.m.",midnight:"midnight",noon:"noon",morning:"morning",afternoon:"afternoon",evening:"evening",night:"night"}},Yl={narrow:{am:"a",pm:"p",midnight:"mi",noon:"n",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"},abbreviated:{am:"AM",pm:"PM",midnight:"midnight",noon:"noon",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"},wide:{am:"a.m.",pm:"p.m.",midnight:"midnight",noon:"noon",morning:"in the morning",afternoon:"in the afternoon",evening:"in the evening",night:"at night"}},ql=(e,t)=>{const n=Number(e),o=n%100;if(o>20||o<10)switch(o%10){case 1:return n+"st";case 2:return n+"nd";case 3:return n+"rd"}return n+"th"},Zl={ordinalNumber:ql,era:ln({values:jl,defaultWidth:"wide"}),quarter:ln({values:Kl,defaultWidth:"wide",argumentCallback:e=>e-1}),month:ln({values:Ul,defaultWidth:"wide"}),day:ln({values:Gl,defaultWidth:"wide"}),dayPeriod:ln({values:Xl,defaultWidth:"wide",formattingValues:Yl,defaultFormattingWidth:"wide"})},Jl=/^(\d+)(th|st|nd|rd)?/i,Ql=/\d+/i,es={narrow:/^(b|a)/i,abbreviated:/^(b\.?\s?c\.?|b\.?\s?c\.?\s?e\.?|a\.?\s?d\.?|c\.?\s?e\.?)/i,wide:/^(before christ|before common era|anno domini|common era)/i},ts={any:[/^b/i,/^(a|c)/i]},ns={narrow:/^[1234]/i,abbreviated:/^q[1234]/i,wide:/^[1234](th|st|nd|rd)? quarter/i},os={any:[/1/i,/2/i,/3/i,/4/i]},rs={narrow:/^[jfmasond]/i,abbreviated:/^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,wide:/^(january|february|march|april|may|june|july|august|september|october|november|december)/i},is={narrow:[/^j/i,/^f/i,/^m/i,/^a/i,/^m/i,/^j/i,/^j/i,/^a/i,/^s/i,/^o/i,/^n/i,/^d/i],any:[/^ja/i,/^f/i,/^mar/i,/^ap/i,/^may/i,/^jun/i,/^jul/i,/^au/i,/^s/i,/^o/i,/^n/i,/^d/i]},as={narrow:/^[smtwf]/i,short:/^(su|mo|tu|we|th|fr|sa)/i,abbreviated:/^(sun|mon|tue|wed|thu|fri|sat)/i,wide:/^(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/i},ls={narrow:[/^s/i,/^m/i,/^t/i,/^w/i,/^t/i,/^f/i,/^s/i],any:[/^su/i,/^m/i,/^tu/i,/^w/i,/^th/i,/^f/i,/^sa/i]},ss={narrow:/^(a|p|mi|n|(in the|at) (morning|afternoon|evening|night))/i,any:/^([ap]\.?\s?m\.?|midnight|noon|(in the|at) (morning|afternoon|evening|night))/i},ds={any:{am:/^a/i,pm:/^p/i,midnight:/^mi/i,noon:/^no/i,morning:/morning/i,afternoon:/afternoon/i,evening:/evening/i,night:/night/i}},cs={ordinalNumber:Ll({matchPattern:Jl,parsePattern:Ql,valueCallback:e=>parseInt(e,10)}),era:sn({matchPatterns:es,defaultMatchWidth:"wide",parsePatterns:ts,defaultParseWidth:"any"}),quarter:sn({matchPatterns:ns,defaultMatchWidth:"wide",parsePatterns:os,defaultParseWidth:"any",valueCallback:e=>e+1}),month:sn({matchPatterns:rs,defaultMatchWidth:"wide",parsePatterns:is,defaultParseWidth:"any"}),day:sn({matchPatterns:as,defaultMatchWidth:"wide",parsePatterns:ls,defaultParseWidth:"any"}),dayPeriod:sn({matchPatterns:ss,defaultMatchWidth:"any",parsePatterns:ds,defaultParseWidth:"any"})},us={full:"EEEE, MMMM do, y",long:"MMMM do, y",medium:"MMM d, y",short:"MM/dd/yyyy"},fs={full:"h:mm:ss a zzzz",long:"h:mm:ss a z",medium:"h:mm:ss a",short:"h:mm a"},hs={full:"{{date}} 'at' {{time}}",long:"{{date}} 'at' {{time}}",medium:"{{date}}, {{time}}",short:"{{date}}, {{time}}"},vs={date:ro({formats:us,defaultWidth:"full"}),time:ro({formats:fs,defaultWidth:"full"}),dateTime:ro({formats:hs,defaultWidth:"full"})},gs={code:"en-US",formatDistance:Nl,formatLong:vs,formatRelative:Hl,localize:Zl,match:cs,options:{weekStartsOn:0,firstWeekContainsDate:1}},ps={name:"en-US",locale:gs};var mo=In(Rn,"WeakMap"),bs=la(Object.keys,Object),ms=Object.prototype,ys=ms.hasOwnProperty;function ws(e){if(!sa(e))return bs(e);var t=[];for(var n in Object(e))ys.call(e,n)&&n!="constructor"&&t.push(n);return t}function Wo(e){return zo(e)?da(e):ws(e)}var xs=/\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/,Cs=/^\w*$/;function No(e,t){if($t(e))return!1;var n=typeof e;return n=="number"||n=="symbol"||n=="boolean"||e==null||Ar(e)?!0:Cs.test(e)||!xs.test(e)||t!=null&&e in Object(t)}var Ss="Expected a function";function Vo(e,t){if(typeof e!="function"||t!=null&&typeof t!="function")throw new TypeError(Ss);var n=function(){var o=arguments,r=t?t.apply(this,o):o[0],a=n.cache;if(a.has(r))return a.get(r);var l=e.apply(this,o);return n.cache=a.set(r,l)||a,l};return n.cache=new(Vo.Cache||Po),n}Vo.Cache=Po;var ks=500;function _s(e){var t=Vo(e,function(o){return n.size===ks&&n.clear(),o}),n=t.cache;return t}var $s=/[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g,zs=/\\(\\)?/g,Ps=_s(function(e){var t=[];return e.charCodeAt(0)===46&&t.push(""),e.replace($s,function(n,o,r,a){t.push(r?a.replace(zs,"$1"):o||n)}),t});function li(e,t){return $t(e)?e:No(e,t)?[e]:Ps(ca(e))}function Ln(e){if(typeof e=="string"||Ar(e))return e;var t=e+"";return t=="0"&&1/e==-1/0?"-0":t}function si(e,t){t=li(t,e);for(var n=0,o=t.length;e!=null&&n<o;)e=e[Ln(t[n++])];return n&&n==o?e:void 0}function Ms(e,t,n){var o=e==null?void 0:si(e,t);return o===void 0?n:o}function Ts(e,t){for(var n=-1,o=t.length,r=e.length;++n<o;)e[r+n]=t[n];return e}function Fs(e,t){for(var n=-1,o=e==null?0:e.length,r=0,a=[];++n<o;){var l=e[n];t(l,n,e)&&(a[r++]=l)}return a}function Os(){return[]}var Bs=Object.prototype,Es=Bs.propertyIsEnumerable,mr=Object.getOwnPropertySymbols,Is=mr?function(e){return e==null?[]:(e=Object(e),Fs(mr(e),function(t){return Es.call(e,t)}))}:Os;function Rs(e,t,n){var o=t(e);return $t(e)?o:Ts(o,n(e))}function yr(e){return Rs(e,Wo,Is)}var yo=In(Rn,"DataView"),wo=In(Rn,"Promise"),xo=In(Rn,"Set"),wr="[object Map]",As="[object Object]",xr="[object Promise]",Cr="[object Set]",Sr="[object WeakMap]",kr="[object DataView]",Ds=Jt(yo),Ls=Jt(vo),Ws=Jt(wo),Ns=Jt(xo),Vs=Jt(mo),St=Dr;(yo&&St(new yo(new ArrayBuffer(1)))!=kr||vo&&St(new vo)!=wr||wo&&St(wo.resolve())!=xr||xo&&St(new xo)!=Cr||mo&&St(new mo)!=Sr)&&(St=function(e){var t=Dr(e),n=t==As?e.constructor:void 0,o=n?Jt(n):"";if(o)switch(o){case Ds:return kr;case Ls:return wr;case Ws:return xr;case Ns:return Cr;case Vs:return Sr}return t});var Hs="__lodash_hash_undefined__";function js(e){return this.__data__.set(e,Hs),this}function Ks(e){return this.__data__.has(e)}function Fn(e){var t=-1,n=e==null?0:e.length;for(this.__data__=new Po;++t<n;)this.add(e[t])}Fn.prototype.add=Fn.prototype.push=js;Fn.prototype.has=Ks;function Us(e,t){for(var n=-1,o=e==null?0:e.length;++n<o;)if(t(e[n],n,e))return!0;return!1}function Gs(e,t){return e.has(t)}var Xs=1,Ys=2;function di(e,t,n,o,r,a){var l=n&Xs,i=e.length,s=t.length;if(i!=s&&!(l&&s>i))return!1;var c=a.get(e),f=a.get(t);if(c&&f)return c==t&&f==e;var u=-1,p=!0,y=n&Ys?new Fn:void 0;for(a.set(e,t),a.set(t,e);++u<i;){var h=e[u],b=t[u];if(o)var w=l?o(b,h,u,t,e,a):o(h,b,u,e,t,a);if(w!==void 0){if(w)continue;p=!1;break}if(y){if(!Us(t,function(m,B){if(!Gs(y,B)&&(h===m||r(h,m,n,o,a)))return y.push(B)})){p=!1;break}}else if(!(h===b||r(h,b,n,o,a))){p=!1;break}}return a.delete(e),a.delete(t),p}function qs(e){var t=-1,n=Array(e.size);return e.forEach(function(o,r){n[++t]=[r,o]}),n}function Zs(e){var t=-1,n=Array(e.size);return e.forEach(function(o){n[++t]=o}),n}var Js=1,Qs=2,ed="[object Boolean]",td="[object Date]",nd="[object Error]",od="[object Map]",rd="[object Number]",id="[object RegExp]",ad="[object Set]",ld="[object String]",sd="[object Symbol]",dd="[object ArrayBuffer]",cd="[object DataView]",_r=Xo?Xo.prototype:void 0,io=_r?_r.valueOf:void 0;function ud(e,t,n,o,r,a,l){switch(n){case cd:if(e.byteLength!=t.byteLength||e.byteOffset!=t.byteOffset)return!1;e=e.buffer,t=t.buffer;case dd:return!(e.byteLength!=t.byteLength||!a(new Yo(e),new Yo(t)));case ed:case td:case rd:return ua(+e,+t);case nd:return e.name==t.name&&e.message==t.message;case id:case ld:return e==t+"";case od:var i=qs;case ad:var s=o&Js;if(i||(i=Zs),e.size!=t.size&&!s)return!1;var c=l.get(e);if(c)return c==t;o|=Qs,l.set(e,t);var f=di(i(e),i(t),o,r,a,l);return l.delete(e),f;case sd:if(io)return io.call(e)==io.call(t)}return!1}var fd=1,hd=Object.prototype,vd=hd.hasOwnProperty;function gd(e,t,n,o,r,a){var l=n&fd,i=yr(e),s=i.length,c=yr(t),f=c.length;if(s!=f&&!l)return!1;for(var u=s;u--;){var p=i[u];if(!(l?p in t:vd.call(t,p)))return!1}var y=a.get(e),h=a.get(t);if(y&&h)return y==t&&h==e;var b=!0;a.set(e,t),a.set(t,e);for(var w=l;++u<s;){p=i[u];var m=e[p],B=t[p];if(o)var W=l?o(B,m,p,t,e,a):o(m,B,p,e,t,a);if(!(W===void 0?m===B||r(m,B,n,o,a):W)){b=!1;break}w||(w=p=="constructor")}if(b&&!w){var F=e.constructor,C=t.constructor;F!=C&&"constructor"in e&&"constructor"in t&&!(typeof F=="function"&&F instanceof F&&typeof C=="function"&&C instanceof C)&&(b=!1)}return a.delete(e),a.delete(t),b}var pd=1,$r="[object Arguments]",zr="[object Array]",Cn="[object Object]",bd=Object.prototype,Pr=bd.hasOwnProperty;function md(e,t,n,o,r,a){var l=$t(e),i=$t(t),s=l?zr:St(e),c=i?zr:St(t);s=s==$r?Cn:s,c=c==$r?Cn:c;var f=s==Cn,u=c==Cn,p=s==c;if(p&&qo(e)){if(!qo(t))return!1;l=!0,f=!1}if(p&&!f)return a||(a=new _n),l||fa(e)?di(e,t,n,o,r,a):ud(e,t,s,n,o,r,a);if(!(n&pd)){var y=f&&Pr.call(e,"__wrapped__"),h=u&&Pr.call(t,"__wrapped__");if(y||h){var b=y?e.value():e,w=h?t.value():t;return a||(a=new _n),r(b,w,n,o,a)}}return p?(a||(a=new _n),gd(e,t,n,o,r,a)):!1}function Ho(e,t,n,o,r){return e===t?!0:e==null||t==null||!Zo(e)&&!Zo(t)?e!==e&&t!==t:md(e,t,n,o,Ho,r)}var yd=1,wd=2;function xd(e,t,n,o){var r=n.length,a=r;if(e==null)return!a;for(e=Object(e);r--;){var l=n[r];if(l[2]?l[1]!==e[l[0]]:!(l[0]in e))return!1}for(;++r<a;){l=n[r];var i=l[0],s=e[i],c=l[1];if(l[2]){if(s===void 0&&!(i in e))return!1}else{var f=new _n,u;if(!(u===void 0?Ho(c,s,yd|wd,o,f):u))return!1}}return!0}function ci(e){return e===e&&!ha(e)}function Cd(e){for(var t=Wo(e),n=t.length;n--;){var o=t[n],r=e[o];t[n]=[o,r,ci(r)]}return t}function ui(e,t){return function(n){return n==null?!1:n[e]===t&&(t!==void 0||e in Object(n))}}function Sd(e){var t=Cd(e);return t.length==1&&t[0][2]?ui(t[0][0],t[0][1]):function(n){return n===e||xd(n,e,t)}}function kd(e,t){return e!=null&&t in Object(e)}function _d(e,t,n){t=li(t,e);for(var o=-1,r=t.length,a=!1;++o<r;){var l=Ln(t[o]);if(!(a=e!=null&&n(e,l)))break;e=e[l]}return a||++o!=r?a:(r=e==null?0:e.length,!!r&&va(r)&&ga(l,r)&&($t(e)||pa(e)))}function $d(e,t){return e!=null&&_d(e,t,kd)}var zd=1,Pd=2;function Md(e,t){return No(e)&&ci(t)?ui(Ln(e),t):function(n){var o=Ms(n,e);return o===void 0&&o===t?$d(n,e):Ho(t,o,zd|Pd)}}function Td(e){return function(t){return t==null?void 0:t[e]}}function Fd(e){return function(t){return si(t,e)}}function Od(e){return No(e)?Td(Ln(e)):Fd(e)}function Bd(e){return typeof e=="function"?e:e==null?ba:typeof e=="object"?$t(e)?Md(e[0],e[1]):Sd(e):Od(e)}function Ed(e,t){return e&&ma(e,t,Wo)}function Id(e,t){return function(n,o){if(n==null)return n;if(!zo(n))return e(n,o);for(var r=n.length,a=-1,l=Object(n);++a<r&&o(l[a],a,l)!==!1;);return n}}var Rd=Id(Ed);function Ad(e,t){var n=-1,o=zo(e)?Array(e.length):[];return Rd(e,function(r,a,l){o[++n]=t(r,a,l)}),o}function Dd(e,t){var n=$t(e)?ya:Ad;return n(e,Bd(t))}function jo(e){const{mergedLocaleRef:t,mergedDateLocaleRef:n}=We(wa,null)||{},o=H(()=>{var a,l;return(l=(a=t==null?void 0:t.value)===null||a===void 0?void 0:a[e])!==null&&l!==void 0?l:Rl[e]});return{dateLocaleRef:H(()=>{var a;return(a=n==null?void 0:n.value)!==null&&a!==void 0?a:ps}),localeRef:o}}const Ld=Se({name:"Checkmark",render(){return d("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 16 16"},d("g",{fill:"none"},d("path",{d:"M14.046 3.486a.75.75 0 0 1-.032 1.06l-7.93 7.474a.85.85 0 0 1-1.188-.022l-2.68-2.72a.75.75 0 1 1 1.068-1.053l2.234 2.267l7.468-7.038a.75.75 0 0 1 1.06.032z",fill:"currentColor"})))}}),Wd=Se({name:"ChevronDown",render(){return d("svg",{viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg"},d("path",{d:"M3.14645 5.64645C3.34171 5.45118 3.65829 5.45118 3.85355 5.64645L8 9.79289L12.1464 5.64645C12.3417 5.45118 12.6583 5.45118 12.8536 5.64645C13.0488 5.84171 13.0488 6.15829 12.8536 6.35355L8.35355 10.8536C8.15829 11.0488 7.84171 11.0488 7.64645 10.8536L3.14645 6.35355C2.95118 6.15829 2.95118 5.84171 3.14645 5.64645Z",fill:"currentColor"}))}}),Nd=xa("clear",()=>d("svg",{viewBox:"0 0 16 16",version:"1.1",xmlns:"http://www.w3.org/2000/svg"},d("g",{stroke:"none","stroke-width":"1",fill:"none","fill-rule":"evenodd"},d("g",{fill:"currentColor","fill-rule":"nonzero"},d("path",{d:"M8,2 C11.3137085,2 14,4.6862915 14,8 C14,11.3137085 11.3137085,14 8,14 C4.6862915,14 2,11.3137085 2,8 C2,4.6862915 4.6862915,2 8,2 Z M6.5343055,5.83859116 C6.33943736,5.70359511 6.07001296,5.72288026 5.89644661,5.89644661 L5.89644661,5.89644661 L5.83859116,5.9656945 C5.70359511,6.16056264 5.72288026,6.42998704 5.89644661,6.60355339 L5.89644661,6.60355339 L7.293,8 L5.89644661,9.39644661 L5.83859116,9.4656945 C5.70359511,9.66056264 5.72288026,9.92998704 5.89644661,10.1035534 L5.89644661,10.1035534 L5.9656945,10.1614088 C6.16056264,10.2964049 6.42998704,10.2771197 6.60355339,10.1035534 L6.60355339,10.1035534 L8,8.707 L9.39644661,10.1035534 L9.4656945,10.1614088 C9.66056264,10.2964049 9.92998704,10.2771197 10.1035534,10.1035534 L10.1035534,10.1035534 L10.1614088,10.0343055 C10.2964049,9.83943736 10.2771197,9.57001296 10.1035534,9.39644661 L10.1035534,9.39644661 L8.707,8 L10.1035534,6.60355339 L10.1614088,6.5343055 C10.2964049,6.33943736 10.2771197,6.07001296 10.1035534,5.89644661 L10.1035534,5.89644661 L10.0343055,5.83859116 C9.83943736,5.70359511 9.57001296,5.72288026 9.39644661,5.89644661 L9.39644661,5.89644661 L8,7.293 L6.60355339,5.89644661 Z"}))))),Vd=Se({name:"Empty",render(){return d("svg",{viewBox:"0 0 28 28",fill:"none",xmlns:"http://www.w3.org/2000/svg"},d("path",{d:"M26 7.5C26 11.0899 23.0899 14 19.5 14C15.9101 14 13 11.0899 13 7.5C13 3.91015 15.9101 1 19.5 1C23.0899 1 26 3.91015 26 7.5ZM16.8536 4.14645C16.6583 3.95118 16.3417 3.95118 16.1464 4.14645C15.9512 4.34171 15.9512 4.65829 16.1464 4.85355L18.7929 7.5L16.1464 10.1464C15.9512 10.3417 15.9512 10.6583 16.1464 10.8536C16.3417 11.0488 16.6583 11.0488 16.8536 10.8536L19.5 8.20711L22.1464 10.8536C22.3417 11.0488 22.6583 11.0488 22.8536 10.8536C23.0488 10.6583 23.0488 10.3417 22.8536 10.1464L20.2071 7.5L22.8536 4.85355C23.0488 4.65829 23.0488 4.34171 22.8536 4.14645C22.6583 3.95118 22.3417 3.95118 22.1464 4.14645L19.5 6.79289L16.8536 4.14645Z",fill:"currentColor"}),d("path",{d:"M25 22.75V12.5991C24.5572 13.0765 24.053 13.4961 23.5 13.8454V16H17.5L17.3982 16.0068C17.0322 16.0565 16.75 16.3703 16.75 16.75C16.75 18.2688 15.5188 19.5 14 19.5C12.4812 19.5 11.25 18.2688 11.25 16.75L11.2432 16.6482C11.1935 16.2822 10.8797 16 10.5 16H4.5V7.25C4.5 6.2835 5.2835 5.5 6.25 5.5H12.2696C12.4146 4.97463 12.6153 4.47237 12.865 4H6.25C4.45507 4 3 5.45507 3 7.25V22.75C3 24.5449 4.45507 26 6.25 26H21.75C23.5449 26 25 24.5449 25 22.75ZM4.5 22.75V17.5H9.81597L9.85751 17.7041C10.2905 19.5919 11.9808 21 14 21L14.215 20.9947C16.2095 20.8953 17.842 19.4209 18.184 17.5H23.5V22.75C23.5 23.7165 22.7165 24.5 21.75 24.5H6.25C5.2835 24.5 4.5 23.7165 4.5 22.75Z",fill:"currentColor"}))}}),Hd=Se({name:"Eye",render(){return d("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 512 512"},d("path",{d:"M255.66 112c-77.94 0-157.89 45.11-220.83 135.33a16 16 0 0 0-.27 17.77C82.92 340.8 161.8 400 255.66 400c92.84 0 173.34-59.38 221.79-135.25a16.14 16.14 0 0 0 0-17.47C428.89 172.28 347.8 112 255.66 112z",fill:"none",stroke:"currentColor","stroke-linecap":"round","stroke-linejoin":"round","stroke-width":"32"}),d("circle",{cx:"256",cy:"256",r:"80",fill:"none",stroke:"currentColor","stroke-miterlimit":"10","stroke-width":"32"}))}}),jd=Se({name:"EyeOff",render(){return d("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 512 512"},d("path",{d:"M432 448a15.92 15.92 0 0 1-11.31-4.69l-352-352a16 16 0 0 1 22.62-22.62l352 352A16 16 0 0 1 432 448z",fill:"currentColor"}),d("path",{d:"M255.66 384c-41.49 0-81.5-12.28-118.92-36.5c-34.07-22-64.74-53.51-88.7-91v-.08c19.94-28.57 41.78-52.73 65.24-72.21a2 2 0 0 0 .14-2.94L93.5 161.38a2 2 0 0 0-2.71-.12c-24.92 21-48.05 46.76-69.08 76.92a31.92 31.92 0 0 0-.64 35.54c26.41 41.33 60.4 76.14 98.28 100.65C162 402 207.9 416 255.66 416a239.13 239.13 0 0 0 75.8-12.58a2 2 0 0 0 .77-3.31l-21.58-21.58a4 4 0 0 0-3.83-1a204.8 204.8 0 0 1-51.16 6.47z",fill:"currentColor"}),d("path",{d:"M490.84 238.6c-26.46-40.92-60.79-75.68-99.27-100.53C349 110.55 302 96 255.66 96a227.34 227.34 0 0 0-74.89 12.83a2 2 0 0 0-.75 3.31l21.55 21.55a4 4 0 0 0 3.88 1a192.82 192.82 0 0 1 50.21-6.69c40.69 0 80.58 12.43 118.55 37c34.71 22.4 65.74 53.88 89.76 91a.13.13 0 0 1 0 .16a310.72 310.72 0 0 1-64.12 72.73a2 2 0 0 0-.15 2.95l19.9 19.89a2 2 0 0 0 2.7.13a343.49 343.49 0 0 0 68.64-78.48a32.2 32.2 0 0 0-.1-34.78z",fill:"currentColor"}),d("path",{d:"M256 160a95.88 95.88 0 0 0-21.37 2.4a2 2 0 0 0-1 3.38l112.59 112.56a2 2 0 0 0 3.38-1A96 96 0 0 0 256 160z",fill:"currentColor"}),d("path",{d:"M165.78 233.66a2 2 0 0 0-3.38 1a96 96 0 0 0 115 115a2 2 0 0 0 1-3.38z",fill:"currentColor"}))}}),Kd=N("base-clear",`
 flex-shrink: 0;
 height: 1em;
 width: 1em;
 position: relative;
`,[D(">",[_("clear",`
 font-size: var(--n-clear-size);
 height: 1em;
 width: 1em;
 cursor: pointer;
 color: var(--n-clear-color);
 transition: color .3s var(--n-bezier);
 display: flex;
 `,[D("&:hover",`
 color: var(--n-clear-color-hover)!important;
 `),D("&:active",`
 color: var(--n-clear-color-pressed)!important;
 `)]),_("placeholder",`
 display: flex;
 `),_("clear, placeholder",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[zn({originalTransform:"translateX(-50%) translateY(-50%)",left:"50%",top:"50%"})])])]),Co=Se({name:"BaseClear",props:{clsPrefix:{type:String,required:!0},show:Boolean,onClear:Function},setup(e){return To("-base-clear",Kd,_e(e,"clsPrefix")),{handleMouseDown(t){t.preventDefault()}}},render(){const{clsPrefix:e}=this;return d("div",{class:`${e}-base-clear`},d(Mo,null,{default:()=>{var t,n;return this.show?d("div",{key:"dismiss",class:`${e}-base-clear__clear`,onClick:this.onClear,onMousedown:this.handleMouseDown,"data-clear":!0},Yt(this.$slots.icon,()=>[d(Zt,{clsPrefix:e},{default:()=>d(Nd,null)})])):d("div",{key:"icon",class:`${e}-base-clear__placeholder`},(n=(t=this.$slots).placeholder)===null||n===void 0?void 0:n.call(t))}}))}}),Ud=Se({props:{onFocus:Function,onBlur:Function},setup(e){return()=>d("div",{style:"width: 0; height: 0",tabindex:0,onFocus:e.onFocus,onBlur:e.onBlur})}});function Mr(e){return Array.isArray(e)?e:[e]}const So={STOP:"STOP"};function fi(e,t){const n=t(e);e.children!==void 0&&n!==So.STOP&&e.children.forEach(o=>fi(o,t))}function Gd(e,t={}){const{preserveGroup:n=!1}=t,o=[],r=n?l=>{l.isLeaf||(o.push(l.key),a(l.children))}:l=>{l.isLeaf||(l.isGroup||o.push(l.key),a(l.children))};function a(l){l.forEach(r)}return a(e),o}function Xd(e,t){const{isLeaf:n}=e;return n!==void 0?n:!t(e)}function Yd(e){return e.children}function qd(e){return e.key}function Zd(){return!1}function Jd(e,t){const{isLeaf:n}=e;return!(n===!1&&!Array.isArray(t(e)))}function Qd(e){return e.disabled===!0}function ec(e,t){return e.isLeaf===!1&&!Array.isArray(t(e))}function ao(e){var t;return e==null?[]:Array.isArray(e)?e:(t=e.checkedKeys)!==null&&t!==void 0?t:[]}function lo(e){var t;return e==null||Array.isArray(e)?[]:(t=e.indeterminateKeys)!==null&&t!==void 0?t:[]}function tc(e,t){const n=new Set(e);return t.forEach(o=>{n.has(o)||n.add(o)}),Array.from(n)}function nc(e,t){const n=new Set(e);return t.forEach(o=>{n.has(o)&&n.delete(o)}),Array.from(n)}function oc(e){return(e==null?void 0:e.type)==="group"}function rc(e){const t=new Map;return e.forEach((n,o)=>{t.set(n.key,o)}),n=>{var o;return(o=t.get(n))!==null&&o!==void 0?o:null}}class ic extends Error{constructor(){super(),this.message="SubtreeNotLoadedError: checking a subtree whose required nodes are not fully loaded."}}function ac(e,t,n,o){return On(t.concat(e),n,o,!1)}function lc(e,t){const n=new Set;return e.forEach(o=>{const r=t.treeNodeMap.get(o);if(r!==void 0){let a=r.parent;for(;a!==null&&!(a.disabled||n.has(a.key));)n.add(a.key),a=a.parent}}),n}function sc(e,t,n,o){const r=On(t,n,o,!1),a=On(e,n,o,!0),l=lc(e,n),i=[];return r.forEach(s=>{(a.has(s)||l.has(s))&&i.push(s)}),i.forEach(s=>r.delete(s)),r}function so(e,t){const{checkedKeys:n,keysToCheck:o,keysToUncheck:r,indeterminateKeys:a,cascade:l,leafOnly:i,checkStrategy:s,allowNotLoaded:c}=e;if(!l)return o!==void 0?{checkedKeys:tc(n,o),indeterminateKeys:Array.from(a)}:r!==void 0?{checkedKeys:nc(n,r),indeterminateKeys:Array.from(a)}:{checkedKeys:Array.from(n),indeterminateKeys:Array.from(a)};const{levelTreeNodeMap:f}=t;let u;r!==void 0?u=sc(r,n,t,c):o!==void 0?u=ac(o,n,t,c):u=On(n,t,c,!1);const p=s==="parent",y=s==="child"||i,h=u,b=new Set,w=Math.max.apply(null,Array.from(f.keys()));for(let m=w;m>=0;m-=1){const B=m===0,W=f.get(m);for(const F of W){if(F.isLeaf)continue;const{key:C,shallowLoaded:P}=F;if(y&&P&&F.children.forEach(R=>{!R.disabled&&!R.isLeaf&&R.shallowLoaded&&h.has(R.key)&&h.delete(R.key)}),F.disabled||!P)continue;let V=!0,S=!1,k=!0;for(const R of F.children){const K=R.key;if(!R.disabled){if(k&&(k=!1),h.has(K))S=!0;else if(b.has(K)){S=!0,V=!1;break}else if(V=!1,S)break}}V&&!k?(p&&F.children.forEach(R=>{!R.disabled&&h.has(R.key)&&h.delete(R.key)}),h.add(C)):S&&b.add(C),B&&y&&h.has(C)&&h.delete(C)}}return{checkedKeys:Array.from(h),indeterminateKeys:Array.from(b)}}function On(e,t,n,o){const{treeNodeMap:r,getChildren:a}=t,l=new Set,i=new Set(e);return e.forEach(s=>{const c=r.get(s);c!==void 0&&fi(c,f=>{if(f.disabled)return So.STOP;const{key:u}=f;if(!l.has(u)&&(l.add(u),i.add(u),ec(f.rawNode,a))){if(o)return So.STOP;if(!n)throw new ic}})}),i}function dc(e,{includeGroup:t=!1,includeSelf:n=!0},o){var r;const a=o.treeNodeMap;let l=e==null?null:(r=a.get(e))!==null&&r!==void 0?r:null;const i={keyPath:[],treeNodePath:[],treeNode:l};if(l!=null&&l.ignored)return i.treeNode=null,i;for(;l;)!l.ignored&&(t||!l.isGroup)&&i.treeNodePath.push(l),l=l.parent;return i.treeNodePath.reverse(),n||i.treeNodePath.pop(),i.keyPath=i.treeNodePath.map(s=>s.key),i}function cc(e){if(e.length===0)return null;const t=e[0];return t.isGroup||t.ignored||t.disabled?t.getNext():t}function uc(e,t){const n=e.siblings,o=n.length,{index:r}=e;return t?n[(r+1)%o]:r===n.length-1?null:n[r+1]}function Tr(e,t,{loop:n=!1,includeDisabled:o=!1}={}){const r=t==="prev"?fc:uc,a={reverse:t==="prev"};let l=!1,i=null;function s(c){if(c!==null){if(c===e){if(!l)l=!0;else if(!e.disabled&&!e.isGroup){i=e;return}}else if((!c.disabled||o)&&!c.ignored&&!c.isGroup){i=c;return}if(c.isGroup){const f=Ko(c,a);f!==null?i=f:s(r(c,n))}else{const f=r(c,!1);if(f!==null)s(f);else{const u=hc(c);u!=null&&u.isGroup?s(r(u,n)):n&&s(r(c,!0))}}}}return s(e),i}function fc(e,t){const n=e.siblings,o=n.length,{index:r}=e;return t?n[(r-1+o)%o]:r===0?null:n[r-1]}function hc(e){return e.parent}function Ko(e,t={}){const{reverse:n=!1}=t,{children:o}=e;if(o){const{length:r}=o,a=n?r-1:0,l=n?-1:r,i=n?-1:1;for(let s=a;s!==l;s+=i){const c=o[s];if(!c.disabled&&!c.ignored)if(c.isGroup){const f=Ko(c,t);if(f!==null)return f}else return c}}return null}const vc={getChild(){return this.ignored?null:Ko(this)},getParent(){const{parent:e}=this;return e!=null&&e.isGroup?e.getParent():e},getNext(e={}){return Tr(this,"next",e)},getPrev(e={}){return Tr(this,"prev",e)}};function gc(e,t){const n=t?new Set(t):void 0,o=[];function r(a){a.forEach(l=>{o.push(l),!(l.isLeaf||!l.children||l.ignored)&&(l.isGroup||n===void 0||n.has(l.key))&&r(l.children)})}return r(e),o}function pc(e,t){const n=e.key;for(;t;){if(t.key===n)return!0;t=t.parent}return!1}function hi(e,t,n,o,r,a=null,l=0){const i=[];return e.forEach((s,c)=>{var f;const u=Object.create(o);if(u.rawNode=s,u.siblings=i,u.level=l,u.index=c,u.isFirstChild=c===0,u.isLastChild=c+1===e.length,u.parent=a,!u.ignored){const p=r(s);Array.isArray(p)&&(u.children=hi(p,t,n,o,r,u,l+1))}i.push(u),t.set(u.key,u),n.has(l)||n.set(l,[]),(f=n.get(l))===null||f===void 0||f.push(u)}),i}function bc(e,t={}){var n;const o=new Map,r=new Map,{getDisabled:a=Qd,getIgnored:l=Zd,getIsGroup:i=oc,getKey:s=qd}=t,c=(n=t.getChildren)!==null&&n!==void 0?n:Yd,f=t.ignoreEmptyChildren?F=>{const C=c(F);return Array.isArray(C)?C.length?C:null:C}:c,u=Object.assign({get key(){return s(this.rawNode)},get disabled(){return a(this.rawNode)},get isGroup(){return i(this.rawNode)},get isLeaf(){return Xd(this.rawNode,f)},get shallowLoaded(){return Jd(this.rawNode,f)},get ignored(){return l(this.rawNode)},contains(F){return pc(this,F)}},vc),p=hi(e,o,r,u,f);function y(F){if(F==null)return null;const C=o.get(F);return C&&!C.isGroup&&!C.ignored?C:null}function h(F){if(F==null)return null;const C=o.get(F);return C&&!C.ignored?C:null}function b(F,C){const P=h(F);return P?P.getPrev(C):null}function w(F,C){const P=h(F);return P?P.getNext(C):null}function m(F){const C=h(F);return C?C.getParent():null}function B(F){const C=h(F);return C?C.getChild():null}const W={treeNodes:p,treeNodeMap:o,levelTreeNodeMap:r,maxLevel:Math.max(...r.keys()),getChildren:f,getFlattenedNodes(F){return gc(p,F)},getNode:y,getPrev:b,getNext:w,getParent:m,getChild:B,getFirstAvailableNode(){return cc(p)},getPath(F,C={}){return dc(F,C,W)},getCheckedKeys(F,C={}){const{cascade:P=!0,leafOnly:V=!1,checkStrategy:S="all",allowNotLoaded:k=!1}=C;return so({checkedKeys:ao(F),indeterminateKeys:lo(F),cascade:P,leafOnly:V,checkStrategy:S,allowNotLoaded:k},W)},check(F,C,P={}){const{cascade:V=!0,leafOnly:S=!1,checkStrategy:k="all",allowNotLoaded:R=!1}=P;return so({checkedKeys:ao(C),indeterminateKeys:lo(C),keysToCheck:F==null?[]:Mr(F),cascade:V,leafOnly:S,checkStrategy:k,allowNotLoaded:R},W)},uncheck(F,C,P={}){const{cascade:V=!0,leafOnly:S=!1,checkStrategy:k="all",allowNotLoaded:R=!1}=P;return so({checkedKeys:ao(C),indeterminateKeys:lo(C),keysToUncheck:F==null?[]:Mr(F),cascade:V,leafOnly:S,checkStrategy:k,allowNotLoaded:R},W)},getNonLeafKeys(F={}){return Gd(p,F)}};return W}const mc=N("empty",`
 display: flex;
 flex-direction: column;
 align-items: center;
 font-size: var(--n-font-size);
`,[_("icon",`
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 line-height: var(--n-icon-size);
 color: var(--n-icon-color);
 transition:
 color .3s var(--n-bezier);
 `,[D("+",[_("description",`
 margin-top: 8px;
 `)])]),_("description",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),_("extra",`
 text-align: center;
 transition: color .3s var(--n-bezier);
 margin-top: 12px;
 color: var(--n-extra-text-color);
 `)]),yc=Object.assign(Object.assign({},Be.props),{description:String,showDescription:{type:Boolean,default:!0},showIcon:{type:Boolean,default:!0},size:{type:String,default:"medium"},renderIcon:Function}),wc=Se({name:"Empty",props:yc,slots:Object,setup(e){const{mergedClsPrefixRef:t,inlineThemeDisabled:n,mergedComponentPropsRef:o}=ot(e),r=Be("Empty","-empty",mc,Ca,e,t),{localeRef:a}=jo("Empty"),l=H(()=>{var f,u,p;return(f=e.description)!==null&&f!==void 0?f:(p=(u=o==null?void 0:o.value)===null||u===void 0?void 0:u.Empty)===null||p===void 0?void 0:p.description}),i=H(()=>{var f,u;return((u=(f=o==null?void 0:o.value)===null||f===void 0?void 0:f.Empty)===null||u===void 0?void 0:u.renderIcon)||(()=>d(Vd,null))}),s=H(()=>{const{size:f}=e,{common:{cubicBezierEaseInOut:u},self:{[q("iconSize",f)]:p,[q("fontSize",f)]:y,textColor:h,iconColor:b,extraTextColor:w}}=r.value;return{"--n-icon-size":p,"--n-font-size":y,"--n-bezier":u,"--n-text-color":h,"--n-icon-color":b,"--n-extra-text-color":w}}),c=n?at("empty",H(()=>{let f="";const{size:u}=e;return f+=u[0],f}),s,e):void 0;return{mergedClsPrefix:t,mergedRenderIcon:i,localizedDescription:H(()=>l.value||a.value.description),cssVars:n?void 0:s,themeClass:c==null?void 0:c.themeClass,onRender:c==null?void 0:c.onRender}},render(){const{$slots:e,mergedClsPrefix:t,onRender:n}=this;return n==null||n(),d("div",{class:[`${t}-empty`,this.themeClass],style:this.cssVars},this.showIcon?d("div",{class:`${t}-empty__icon`},e.icon?e.icon():d(Zt,{clsPrefix:t},{default:this.mergedRenderIcon})):null,this.showDescription?d("div",{class:`${t}-empty__description`},e.default?e.default():this.localizedDescription):null,e.extra?d("div",{class:`${t}-empty__extra`},e.extra()):null)}}),Fr=Se({name:"NBaseSelectGroupHeader",props:{clsPrefix:{type:String,required:!0},tmNode:{type:Object,required:!0}},setup(){const{renderLabelRef:e,renderOptionRef:t,labelFieldRef:n,nodePropsRef:o}=We(Oo);return{labelField:n,nodeProps:o,renderLabel:e,renderOption:t}},render(){const{clsPrefix:e,renderLabel:t,renderOption:n,nodeProps:o,tmNode:{rawNode:r}}=this,a=o==null?void 0:o(r),l=t?t(r,!1):Gt(r[this.labelField],r,!1),i=d("div",Object.assign({},a,{class:[`${e}-base-select-group-header`,a==null?void 0:a.class]}),l);return r.render?r.render({node:i,option:r}):n?n({node:i,option:r,selected:!1}):i}});function xc(e,t){return d(Qt,{name:"fade-in-scale-up-transition"},{default:()=>e?d(Zt,{clsPrefix:t,class:`${t}-base-select-option__check`},{default:()=>d(Ld)}):null})}const Or=Se({name:"NBaseSelectOption",props:{clsPrefix:{type:String,required:!0},tmNode:{type:Object,required:!0}},setup(e){const{valueRef:t,pendingTmNodeRef:n,multipleRef:o,valueSetRef:r,renderLabelRef:a,renderOptionRef:l,labelFieldRef:i,valueFieldRef:s,showCheckmarkRef:c,nodePropsRef:f,handleOptionClick:u,handleOptionMouseEnter:p}=We(Oo),y=Ue(()=>{const{value:m}=n;return m?e.tmNode.key===m.key:!1});function h(m){const{tmNode:B}=e;B.disabled||u(m,B)}function b(m){const{tmNode:B}=e;B.disabled||p(m,B)}function w(m){const{tmNode:B}=e,{value:W}=y;B.disabled||W||p(m,B)}return{multiple:o,isGrouped:Ue(()=>{const{tmNode:m}=e,{parent:B}=m;return B&&B.rawNode.type==="group"}),showCheckmark:c,nodeProps:f,isPending:y,isSelected:Ue(()=>{const{value:m}=t,{value:B}=o;if(m===null)return!1;const W=e.tmNode.rawNode[s.value];if(B){const{value:F}=r;return F.has(W)}else return m===W}),labelField:i,renderLabel:a,renderOption:l,handleMouseMove:w,handleMouseEnter:b,handleClick:h}},render(){const{clsPrefix:e,tmNode:{rawNode:t},isSelected:n,isPending:o,isGrouped:r,showCheckmark:a,nodeProps:l,renderOption:i,renderLabel:s,handleClick:c,handleMouseEnter:f,handleMouseMove:u}=this,p=xc(n,e),y=s?[s(t,n),a&&p]:[Gt(t[this.labelField],t,n),a&&p],h=l==null?void 0:l(t),b=d("div",Object.assign({},h,{class:[`${e}-base-select-option`,t.class,h==null?void 0:h.class,{[`${e}-base-select-option--disabled`]:t.disabled,[`${e}-base-select-option--selected`]:n,[`${e}-base-select-option--grouped`]:r,[`${e}-base-select-option--pending`]:o,[`${e}-base-select-option--show-checkmark`]:a}],style:[(h==null?void 0:h.style)||"",t.style||""],onClick:oo([c,h==null?void 0:h.onClick]),onMouseenter:oo([f,h==null?void 0:h.onMouseenter]),onMousemove:oo([u,h==null?void 0:h.onMousemove])}),d("div",{class:`${e}-base-select-option__content`},y));return t.render?t.render({node:b,option:t,selected:n}):i?i({node:b,option:t,selected:n}):b}}),{cubicBezierEaseIn:Br,cubicBezierEaseOut:Er}=en;function vi({transformOrigin:e="inherit",duration:t=".2s",enterScale:n=".9",originalTransform:o="",originalTransition:r=""}={}){return[D("&.fade-in-scale-up-transition-leave-active",{transformOrigin:e,transition:`opacity ${t} ${Br}, transform ${t} ${Br} ${r&&`,${r}`}`}),D("&.fade-in-scale-up-transition-enter-active",{transformOrigin:e,transition:`opacity ${t} ${Er}, transform ${t} ${Er} ${r&&`,${r}`}`}),D("&.fade-in-scale-up-transition-enter-from, &.fade-in-scale-up-transition-leave-to",{opacity:0,transform:`${o} scale(${n})`}),D("&.fade-in-scale-up-transition-leave-from, &.fade-in-scale-up-transition-enter-to",{opacity:1,transform:`${o} scale(1)`})]}const Cc=N("base-select-menu",`
 line-height: 1.5;
 outline: none;
 z-index: 0;
 position: relative;
 border-radius: var(--n-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-color);
`,[N("scrollbar",`
 max-height: var(--n-height);
 `),N("virtual-list",`
 max-height: var(--n-height);
 `),N("base-select-option",`
 min-height: var(--n-option-height);
 font-size: var(--n-option-font-size);
 display: flex;
 align-items: center;
 `,[_("content",`
 z-index: 1;
 white-space: nowrap;
 text-overflow: ellipsis;
 overflow: hidden;
 `)]),N("base-select-group-header",`
 min-height: var(--n-option-height);
 font-size: .93em;
 display: flex;
 align-items: center;
 `),N("base-select-menu-option-wrapper",`
 position: relative;
 width: 100%;
 `),_("loading, empty",`
 display: flex;
 padding: 12px 32px;
 flex: 1;
 justify-content: center;
 `),_("loading",`
 color: var(--n-loading-color);
 font-size: var(--n-loading-size);
 `),_("header",`
 padding: 8px var(--n-option-padding-left);
 font-size: var(--n-option-font-size);
 transition: 
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 border-bottom: 1px solid var(--n-action-divider-color);
 color: var(--n-action-text-color);
 `),_("action",`
 padding: 8px var(--n-option-padding-left);
 font-size: var(--n-option-font-size);
 transition: 
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 border-top: 1px solid var(--n-action-divider-color);
 color: var(--n-action-text-color);
 `),N("base-select-group-header",`
 position: relative;
 cursor: default;
 padding: var(--n-option-padding);
 color: var(--n-group-header-text-color);
 `),N("base-select-option",`
 cursor: pointer;
 position: relative;
 padding: var(--n-option-padding);
 transition:
 color .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 box-sizing: border-box;
 color: var(--n-option-text-color);
 opacity: 1;
 `,[Z("show-checkmark",`
 padding-right: calc(var(--n-option-padding-right) + 20px);
 `),D("&::before",`
 content: "";
 position: absolute;
 left: 4px;
 right: 4px;
 top: 0;
 bottom: 0;
 border-radius: var(--n-border-radius);
 transition: background-color .3s var(--n-bezier);
 `),D("&:active",`
 color: var(--n-option-text-color-pressed);
 `),Z("grouped",`
 padding-left: calc(var(--n-option-padding-left) * 1.5);
 `),Z("pending",[D("&::before",`
 background-color: var(--n-option-color-pending);
 `)]),Z("selected",`
 color: var(--n-option-text-color-active);
 `,[D("&::before",`
 background-color: var(--n-option-color-active);
 `),Z("pending",[D("&::before",`
 background-color: var(--n-option-color-active-pending);
 `)])]),Z("disabled",`
 cursor: not-allowed;
 `,[De("selected",`
 color: var(--n-option-text-color-disabled);
 `),Z("selected",`
 opacity: var(--n-option-opacity-disabled);
 `)]),_("check",`
 font-size: 16px;
 position: absolute;
 right: calc(var(--n-option-padding-right) - 4px);
 top: calc(50% - 7px);
 color: var(--n-option-check-color);
 transition: color .3s var(--n-bezier);
 `,[vi({enterScale:"0.5"})])])]),Sc=Se({name:"InternalSelectMenu",props:Object.assign(Object.assign({},Be.props),{clsPrefix:{type:String,required:!0},scrollable:{type:Boolean,default:!0},treeMate:{type:Object,required:!0},multiple:Boolean,size:{type:String,default:"medium"},value:{type:[String,Number,Array],default:null},autoPending:Boolean,virtualScroll:{type:Boolean,default:!0},show:{type:Boolean,default:!0},labelField:{type:String,default:"label"},valueField:{type:String,default:"value"},loading:Boolean,focusable:Boolean,renderLabel:Function,renderOption:Function,nodeProps:Function,showCheckmark:{type:Boolean,default:!0},onMousedown:Function,onScroll:Function,onFocus:Function,onBlur:Function,onKeyup:Function,onKeydown:Function,onTabOut:Function,onMouseenter:Function,onMouseleave:Function,onResize:Function,resetMenuOnOptionsChange:{type:Boolean,default:!0},inlineThemeDisabled:Boolean,scrollbarProps:Object,onToggle:Function}),setup(e){const{mergedClsPrefixRef:t,mergedRtlRef:n,mergedComponentPropsRef:o}=ot(e),r=It("InternalSelectMenu",n,t),a=Be("InternalSelectMenu","-internal-select-menu",Cc,Sa,e,_e(e,"clsPrefix")),l=T(null),i=T(null),s=T(null),c=H(()=>e.treeMate.getFlattenedNodes()),f=H(()=>rc(c.value)),u=T(null);function p(){const{treeMate:O}=e;let L=null;const{value:pe}=e;pe===null?L=O.getFirstAvailableNode():(e.multiple?L=O.getNode((pe||[])[(pe||[]).length-1]):L=O.getNode(pe),(!L||L.disabled)&&(L=O.getFirstAvailableNode())),J(L||null)}function y(){const{value:O}=u;O&&!e.treeMate.getNode(O.key)&&(u.value=null)}let h;Ie(()=>e.show,O=>{O?h=Ie(()=>e.treeMate,()=>{e.resetMenuOnOptionsChange?(e.autoPending?p():y(),mt(Q)):y()},{immediate:!0}):h==null||h()},{immediate:!0}),Je(()=>{h==null||h()});const b=H(()=>et(a.value.self[q("optionHeight",e.size)])),w=H(()=>Ot(a.value.self[q("padding",e.size)])),m=H(()=>e.multiple&&Array.isArray(e.value)?new Set(e.value):new Set),B=H(()=>{const O=c.value;return O&&O.length===0}),W=H(()=>{var O,L;return(L=(O=o==null?void 0:o.value)===null||O===void 0?void 0:O.Select)===null||L===void 0?void 0:L.renderEmpty});function F(O){const{onToggle:L}=e;L&&L(O)}function C(O){const{onScroll:L}=e;L&&L(O)}function P(O){var L;(L=s.value)===null||L===void 0||L.sync(),C(O)}function V(){var O;(O=s.value)===null||O===void 0||O.sync()}function S(){const{value:O}=u;return O||null}function k(O,L){L.disabled||J(L,!1)}function R(O,L){L.disabled||F(L)}function K(O){var L;cn(O,"action")||(L=e.onKeyup)===null||L===void 0||L.call(e,O)}function j(O){var L;cn(O,"action")||(L=e.onKeydown)===null||L===void 0||L.call(e,O)}function z(O){var L;(L=e.onMousedown)===null||L===void 0||L.call(e,O),!e.focusable&&O.preventDefault()}function G(){const{value:O}=u;O&&J(O.getNext({loop:!0}),!0)}function E(){const{value:O}=u;O&&J(O.getPrev({loop:!0}),!0)}function J(O,L=!1){u.value=O,L&&Q()}function Q(){var O,L;const pe=u.value;if(!pe)return;const fe=f.value(pe.key);fe!==null&&(e.virtualScroll?(O=i.value)===null||O===void 0||O.scrollTo({index:fe}):(L=s.value)===null||L===void 0||L.scrollTo({index:fe,elSize:b.value}))}function X(O){var L,pe;!((L=l.value)===null||L===void 0)&&L.contains(O.target)&&((pe=e.onFocus)===null||pe===void 0||pe.call(e,O))}function te(O){var L,pe;!((L=l.value)===null||L===void 0)&&L.contains(O.relatedTarget)||(pe=e.onBlur)===null||pe===void 0||pe.call(e,O)}Ge(Oo,{handleOptionMouseEnter:k,handleOptionClick:R,valueSetRef:m,pendingTmNodeRef:u,nodePropsRef:_e(e,"nodeProps"),showCheckmarkRef:_e(e,"showCheckmark"),multipleRef:_e(e,"multiple"),valueRef:_e(e,"value"),renderLabelRef:_e(e,"renderLabel"),renderOptionRef:_e(e,"renderOption"),labelFieldRef:_e(e,"labelField"),valueFieldRef:_e(e,"valueField")}),Ge(jr,l),nt(()=>{const{value:O}=s;O&&O.sync()});const ue=H(()=>{const{size:O}=e,{common:{cubicBezierEaseInOut:L},self:{height:pe,borderRadius:fe,color:Me,groupHeaderTextColor:Fe,actionDividerColor:ie,optionTextColorPressed:Ne,optionTextColor:Le,optionTextColorDisabled:Ve,optionTextColorActive:rt,optionOpacityDisabled:it,optionCheckColor:Ke,actionTextColor:Xe,optionColorPending:I,optionColorActive:g,loadingColor:ce,loadingSize:ee,optionColorActivePending:ne,[q("optionFontSize",O)]:ke,[q("optionHeight",O)]:A,[q("optionPadding",O)]:Y}}=a.value;return{"--n-height":pe,"--n-action-divider-color":ie,"--n-action-text-color":Xe,"--n-bezier":L,"--n-border-radius":fe,"--n-color":Me,"--n-option-font-size":ke,"--n-group-header-text-color":Fe,"--n-option-check-color":Ke,"--n-option-color-pending":I,"--n-option-color-active":g,"--n-option-color-active-pending":ne,"--n-option-height":A,"--n-option-opacity-disabled":it,"--n-option-text-color":Le,"--n-option-text-color-active":rt,"--n-option-text-color-disabled":Ve,"--n-option-text-color-pressed":Ne,"--n-option-padding":Y,"--n-option-padding-left":Ot(Y,"left"),"--n-option-padding-right":Ot(Y,"right"),"--n-loading-color":ce,"--n-loading-size":ee}}),{inlineThemeDisabled:le}=e,re=le?at("internal-select-menu",H(()=>e.size[0]),ue,e):void 0,xe={selfRef:l,next:G,prev:E,getPendingTmNode:S};return ii(l,e.onResize),Object.assign({mergedTheme:a,mergedClsPrefix:t,rtlEnabled:r,virtualListRef:i,scrollbarRef:s,itemSize:b,padding:w,flattenedNodes:c,empty:B,mergedRenderEmpty:W,virtualListContainer(){const{value:O}=i;return O==null?void 0:O.listElRef},virtualListContent(){const{value:O}=i;return O==null?void 0:O.itemsElRef},doScroll:C,handleFocusin:X,handleFocusout:te,handleKeyUp:K,handleKeyDown:j,handleMouseDown:z,handleVirtualListResize:V,handleVirtualListScroll:P,cssVars:le?void 0:ue,themeClass:re==null?void 0:re.themeClass,onRender:re==null?void 0:re.onRender},xe)},render(){const{$slots:e,virtualScroll:t,clsPrefix:n,mergedTheme:o,themeClass:r,onRender:a}=this;return a==null||a(),d("div",{ref:"selfRef",tabindex:this.focusable?0:-1,class:[`${n}-base-select-menu`,`${n}-base-select-menu--${this.size}-size`,this.rtlEnabled&&`${n}-base-select-menu--rtl`,r,this.multiple&&`${n}-base-select-menu--multiple`],style:this.cssVars,onFocusin:this.handleFocusin,onFocusout:this.handleFocusout,onKeyup:this.handleKeyUp,onKeydown:this.handleKeyDown,onMousedown:this.handleMouseDown,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},Re(e.header,l=>l&&d("div",{class:`${n}-base-select-menu__header`,"data-header":!0,key:"header"},l)),this.loading?d("div",{class:`${n}-base-select-menu__loading`},d(vn,{clsPrefix:n,strokeWidth:20})):this.empty?d("div",{class:`${n}-base-select-menu__empty`,"data-empty":!0},Yt(e.empty,()=>{var l;return[((l=this.mergedRenderEmpty)===null||l===void 0?void 0:l.call(this))||d(wc,{theme:o.peers.Empty,themeOverrides:o.peerOverrides.Empty,size:this.size})]})):d(An,Object.assign({ref:"scrollbarRef",theme:o.peers.Scrollbar,themeOverrides:o.peerOverrides.Scrollbar,scrollable:this.scrollable,container:t?this.virtualListContainer:void 0,content:t?this.virtualListContent:void 0,onScroll:t?void 0:this.doScroll},this.scrollbarProps),{default:()=>t?d(zl,{ref:"virtualListRef",class:`${n}-virtual-list`,items:this.flattenedNodes,itemSize:this.itemSize,showScrollbar:!1,paddingTop:this.padding.top,paddingBottom:this.padding.bottom,onResize:this.handleVirtualListResize,onScroll:this.handleVirtualListScroll,itemResizable:!0},{default:({item:l})=>l.isGroup?d(Fr,{key:l.key,clsPrefix:n,tmNode:l}):l.ignored?null:d(Or,{clsPrefix:n,key:l.key,tmNode:l})}):d("div",{class:`${n}-base-select-menu-option-wrapper`,style:{paddingTop:this.padding.top,paddingBottom:this.padding.bottom}},this.flattenedNodes.map(l=>l.isGroup?d(Fr,{key:l.key,clsPrefix:n,tmNode:l}):d(Or,{clsPrefix:n,key:l.key,tmNode:l})))}),Re(e.action,l=>l&&[d("div",{class:`${n}-base-select-menu__action`,"data-action":!0,key:"action"},l),d(Ud,{onFocus:this.onTabOut,key:"focus-detector"})]))}}),co={top:"bottom",bottom:"top",left:"right",right:"left"},Ae="var(--n-arrow-height) * 1.414",kc=D([N("popover",`
 transition:
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 position: relative;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 box-shadow: var(--n-box-shadow);
 word-break: break-word;
 `,[D(">",[N("scrollbar",`
 height: inherit;
 max-height: inherit;
 `)]),De("raw",`
 background-color: var(--n-color);
 border-radius: var(--n-border-radius);
 `,[De("scrollable",[De("show-header-or-footer","padding: var(--n-padding);")])]),_("header",`
 padding: var(--n-padding);
 border-bottom: 1px solid var(--n-divider-color);
 transition: border-color .3s var(--n-bezier);
 `),_("footer",`
 padding: var(--n-padding);
 border-top: 1px solid var(--n-divider-color);
 transition: border-color .3s var(--n-bezier);
 `),Z("scrollable, show-header-or-footer",[_("content",`
 padding: var(--n-padding);
 `)])]),N("popover-shared",`
 transform-origin: inherit;
 `,[N("popover-arrow-wrapper",`
 position: absolute;
 overflow: hidden;
 pointer-events: none;
 `,[N("popover-arrow",`
 transition: background-color .3s var(--n-bezier);
 position: absolute;
 display: block;
 width: calc(${Ae});
 height: calc(${Ae});
 box-shadow: 0 0 8px 0 rgba(0, 0, 0, .12);
 transform: rotate(45deg);
 background-color: var(--n-color);
 pointer-events: all;
 `)]),D("&.popover-transition-enter-from, &.popover-transition-leave-to",`
 opacity: 0;
 transform: scale(.85);
 `),D("&.popover-transition-enter-to, &.popover-transition-leave-from",`
 transform: scale(1);
 opacity: 1;
 `),D("&.popover-transition-enter-active",`
 transition:
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 opacity .15s var(--n-bezier-ease-out),
 transform .15s var(--n-bezier-ease-out);
 `),D("&.popover-transition-leave-active",`
 transition:
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 opacity .15s var(--n-bezier-ease-in),
 transform .15s var(--n-bezier-ease-in);
 `)]),Qe("top-start",`
 top: calc(${Ae} / -2);
 left: calc(${pt("top-start")} - var(--v-offset-left));
 `),Qe("top",`
 top: calc(${Ae} / -2);
 transform: translateX(calc(${Ae} / -2)) rotate(45deg);
 left: 50%;
 `),Qe("top-end",`
 top: calc(${Ae} / -2);
 right: calc(${pt("top-end")} + var(--v-offset-left));
 `),Qe("bottom-start",`
 bottom: calc(${Ae} / -2);
 left: calc(${pt("bottom-start")} - var(--v-offset-left));
 `),Qe("bottom",`
 bottom: calc(${Ae} / -2);
 transform: translateX(calc(${Ae} / -2)) rotate(45deg);
 left: 50%;
 `),Qe("bottom-end",`
 bottom: calc(${Ae} / -2);
 right: calc(${pt("bottom-end")} + var(--v-offset-left));
 `),Qe("left-start",`
 left: calc(${Ae} / -2);
 top: calc(${pt("left-start")} - var(--v-offset-top));
 `),Qe("left",`
 left: calc(${Ae} / -2);
 transform: translateY(calc(${Ae} / -2)) rotate(45deg);
 top: 50%;
 `),Qe("left-end",`
 left: calc(${Ae} / -2);
 bottom: calc(${pt("left-end")} + var(--v-offset-top));
 `),Qe("right-start",`
 right: calc(${Ae} / -2);
 top: calc(${pt("right-start")} - var(--v-offset-top));
 `),Qe("right",`
 right: calc(${Ae} / -2);
 transform: translateY(calc(${Ae} / -2)) rotate(45deg);
 top: 50%;
 `),Qe("right-end",`
 right: calc(${Ae} / -2);
 bottom: calc(${pt("right-end")} + var(--v-offset-top));
 `),...Dd({top:["right-start","left-start"],right:["top-end","bottom-end"],bottom:["right-end","left-end"],left:["top-start","bottom-start"]},(e,t)=>{const n=["right","left"].includes(t),o=n?"width":"height";return e.map(r=>{const a=r.split("-")[1]==="end",i=`calc((${`var(--v-target-${o}, 0px)`} - ${Ae}) / 2)`,s=pt(r);return D(`[v-placement="${r}"] >`,[N("popover-shared",[Z("center-arrow",[N("popover-arrow",`${t}: calc(max(${i}, ${s}) ${a?"+":"-"} var(--v-offset-${n?"left":"top"}));`)])])])})})]);function pt(e){return["top","bottom"].includes(e.split("-")[0])?"var(--n-arrow-offset)":"var(--n-arrow-offset-vertical)"}function Qe(e,t){const n=e.split("-")[0],o=["top","bottom"].includes(n)?"height: var(--n-space-arrow);":"width: var(--n-space-arrow);";return D(`[v-placement="${e}"] >`,[N("popover-shared",`
 margin-${co[n]}: var(--n-space);
 `,[Z("show-arrow",`
 margin-${co[n]}: var(--n-space-arrow);
 `),Z("overlap",`
 margin: 0;
 `),ka("popover-arrow-wrapper",`
 right: 0;
 left: 0;
 top: 0;
 bottom: 0;
 ${n}: 100%;
 ${co[n]}: auto;
 ${o}
 `,[N("popover-arrow",t)])])])}const gi=Object.assign(Object.assign({},Be.props),{to:yt.propTo,show:Boolean,trigger:String,showArrow:Boolean,delay:Number,duration:Number,raw:Boolean,arrowPointToCenter:Boolean,arrowClass:String,arrowStyle:[String,Object],arrowWrapperClass:String,arrowWrapperStyle:[String,Object],displayDirective:String,x:Number,y:Number,flip:Boolean,overlap:Boolean,placement:String,width:[Number,String],keepAliveOnHover:Boolean,scrollable:Boolean,contentClass:String,contentStyle:[Object,String],headerClass:String,headerStyle:[Object,String],footerClass:String,footerStyle:[Object,String],internalDeactivateImmediately:Boolean,animated:Boolean,onClickoutside:Function,internalTrapFocus:Boolean,internalOnAfterLeave:Function,minWidth:Number,maxWidth:Number});function _c({arrowClass:e,arrowStyle:t,arrowWrapperClass:n,arrowWrapperStyle:o,clsPrefix:r}){return d("div",{key:"__popover-arrow__",style:o,class:[`${r}-popover-arrow-wrapper`,n]},d("div",{class:[`${r}-popover-arrow`,e],style:t}))}const $c=Se({name:"PopoverBody",inheritAttrs:!1,props:gi,setup(e,{slots:t,attrs:n}){const{namespaceRef:o,mergedClsPrefixRef:r,inlineThemeDisabled:a,mergedRtlRef:l}=ot(e),i=Be("Popover","-popover",kc,_a,e,r),s=It("Popover",l,r),c=T(null),f=We("NPopover"),u=T(null),p=T(e.show),y=T(!1);Bt(()=>{const{show:k}=e;k&&!Fl()&&!e.internalDeactivateImmediately&&(y.value=!0)});const h=H(()=>{const{trigger:k,onClickoutside:R}=e,K=[],{positionManuallyRef:{value:j}}=f;return j||(k==="click"&&!R&&K.push([hn,P,void 0,{capture:!0}]),k==="hover"&&K.push([vl,C])),R&&K.push([hn,P,void 0,{capture:!0}]),(e.displayDirective==="show"||e.animated&&y.value)&&K.push([Pn,e.show]),K}),b=H(()=>{const{common:{cubicBezierEaseInOut:k,cubicBezierEaseIn:R,cubicBezierEaseOut:K},self:{space:j,spaceArrow:z,padding:G,fontSize:E,textColor:J,dividerColor:Q,color:X,boxShadow:te,borderRadius:ue,arrowHeight:le,arrowOffset:re,arrowOffsetVertical:xe}}=i.value;return{"--n-box-shadow":te,"--n-bezier":k,"--n-bezier-ease-in":R,"--n-bezier-ease-out":K,"--n-font-size":E,"--n-text-color":J,"--n-color":X,"--n-divider-color":Q,"--n-border-radius":ue,"--n-arrow-height":le,"--n-arrow-offset":re,"--n-arrow-offset-vertical":xe,"--n-padding":G,"--n-space":j,"--n-space-arrow":z}}),w=H(()=>{const k=e.width==="trigger"?void 0:fn(e.width),R=[];k&&R.push({width:k});const{maxWidth:K,minWidth:j}=e;return K&&R.push({maxWidth:fn(K)}),j&&R.push({maxWidth:fn(j)}),a||R.push(b.value),R}),m=a?at("popover",void 0,b,e):void 0;f.setBodyInstance({syncPosition:B}),Je(()=>{f.setBodyInstance(null)}),Ie(_e(e,"show"),k=>{e.animated||(k?p.value=!0:p.value=!1)});function B(){var k;(k=c.value)===null||k===void 0||k.syncPosition()}function W(k){e.trigger==="hover"&&e.keepAliveOnHover&&e.show&&f.handleMouseEnter(k)}function F(k){e.trigger==="hover"&&e.keepAliveOnHover&&f.handleMouseLeave(k)}function C(k){e.trigger==="hover"&&!V().contains($n(k))&&f.handleMouseMoveOutside(k)}function P(k){(e.trigger==="click"&&!V().contains($n(k))||e.onClickoutside)&&f.handleClickOutside(k)}function V(){return f.getTriggerElement()}Ge(Ro,u),Ge(Bo,null),Ge(Io,null);function S(){if(m==null||m.onRender(),!(e.displayDirective==="show"||e.show||e.animated&&y.value))return null;let R;const K=f.internalRenderBodyRef.value,{value:j}=r;if(K)R=K([`${j}-popover-shared`,(s==null?void 0:s.value)&&`${j}-popover--rtl`,m==null?void 0:m.themeClass.value,e.overlap&&`${j}-popover-shared--overlap`,e.showArrow&&`${j}-popover-shared--show-arrow`,e.arrowPointToCenter&&`${j}-popover-shared--center-arrow`],u,w.value,W,F);else{const{value:z}=f.extraClassRef,{internalTrapFocus:G}=e,E=!qt(t.header)||!qt(t.footer),J=()=>{var Q,X;const te=E?d(je,null,Re(t.header,re=>re?d("div",{class:[`${j}-popover__header`,e.headerClass],style:e.headerStyle},re):null),Re(t.default,re=>re?d("div",{class:[`${j}-popover__content`,e.contentClass],style:e.contentStyle},t):null),Re(t.footer,re=>re?d("div",{class:[`${j}-popover__footer`,e.footerClass],style:e.footerStyle},re):null)):e.scrollable?(Q=t.default)===null||Q===void 0?void 0:Q.call(t):d("div",{class:[`${j}-popover__content`,e.contentClass],style:e.contentStyle},t),ue=e.scrollable?d($a,{themeOverrides:i.value.peerOverrides.Scrollbar,theme:i.value.peers.Scrollbar,contentClass:E?void 0:`${j}-popover__content ${(X=e.contentClass)!==null&&X!==void 0?X:""}`,contentStyle:E?void 0:e.contentStyle},{default:()=>te}):te,le=e.showArrow?_c({arrowClass:e.arrowClass,arrowStyle:e.arrowStyle,arrowWrapperClass:e.arrowWrapperClass,arrowWrapperStyle:e.arrowWrapperStyle,clsPrefix:j}):null;return[ue,le]};R=d("div",$o({class:[`${j}-popover`,`${j}-popover-shared`,(s==null?void 0:s.value)&&`${j}-popover--rtl`,m==null?void 0:m.themeClass.value,z.map(Q=>`${j}-${Q}`),{[`${j}-popover--scrollable`]:e.scrollable,[`${j}-popover--show-header-or-footer`]:E,[`${j}-popover--raw`]:e.raw,[`${j}-popover-shared--overlap`]:e.overlap,[`${j}-popover-shared--show-arrow`]:e.showArrow,[`${j}-popover-shared--center-arrow`]:e.arrowPointToCenter}],ref:u,style:w.value,onKeydown:f.handleKeydown,onMouseenter:W,onMouseleave:F},n),G?d(ri,{active:e.show,autoFocus:!0},{default:J}):J())}return _t(R,h.value)}return{displayed:y,namespace:o,isMounted:f.isMountedRef,zIndex:f.zIndexRef,followerRef:c,adjustedTo:yt(e),followerEnabled:p,renderContentNode:S}},render(){return d(Jr,{ref:"followerRef",zIndex:this.zIndex,show:this.show,enabled:this.followerEnabled,to:this.adjustedTo,x:this.x,y:this.y,flip:this.flip,placement:this.placement,containerClass:this.namespace,overlap:this.overlap,width:this.width==="trigger"?"target":void 0,teleportDisabled:this.adjustedTo===yt.tdkey},{default:()=>this.animated?d(Qt,{name:"popover-transition",appear:this.isMounted,onEnter:()=>{this.followerEnabled=!0},onAfterLeave:()=>{var e;(e=this.internalOnAfterLeave)===null||e===void 0||e.call(this),this.followerEnabled=!1,this.displayed=!1}},{default:this.renderContentNode}):this.renderContentNode()})}}),zc=Object.keys(gi),Pc={focus:["onFocus","onBlur"],click:["onClick"],hover:["onMouseenter","onMouseleave"],manual:[],nested:["onFocus","onBlur","onMouseenter","onMouseleave","onClick"]};function Mc(e,t,n){Pc[t].forEach(o=>{e.props?e.props=Object.assign({},e.props):e.props={};const r=e.props[o],a=n[o];r?e.props[o]=(...l)=>{r(...l),a(...l)}:e.props[o]=a})}const Tc={show:{type:Boolean,default:void 0},defaultShow:Boolean,showArrow:{type:Boolean,default:!0},trigger:{type:String,default:"hover"},delay:{type:Number,default:100},duration:{type:Number,default:100},raw:Boolean,placement:{type:String,default:"top"},x:Number,y:Number,arrowPointToCenter:Boolean,disabled:Boolean,getDisabled:Function,displayDirective:{type:String,default:"if"},arrowClass:String,arrowStyle:[String,Object],arrowWrapperClass:String,arrowWrapperStyle:[String,Object],flip:{type:Boolean,default:!0},animated:{type:Boolean,default:!0},width:{type:[Number,String],default:void 0},overlap:Boolean,keepAliveOnHover:{type:Boolean,default:!0},zIndex:Number,to:yt.propTo,scrollable:Boolean,contentClass:String,contentStyle:[Object,String],headerClass:String,headerStyle:[Object,String],footerClass:String,footerStyle:[Object,String],onClickoutside:Function,"onUpdate:show":[Function,Array],onUpdateShow:[Function,Array],internalDeactivateImmediately:Boolean,internalSyncTargetWithParent:Boolean,internalInheritedEventHandlers:{type:Array,default:()=>[]},internalTrapFocus:Boolean,internalExtraClass:{type:Array,default:()=>[]},onShow:[Function,Array],onHide:[Function,Array],arrow:{type:Boolean,default:void 0},minWidth:Number,maxWidth:Number},Fc=Object.assign(Object.assign(Object.assign({},Be.props),Tc),{internalOnAfterLeave:Function,internalRenderBody:Function}),Oc=Se({name:"Popover",inheritAttrs:!1,props:Fc,slots:Object,__popover__:!0,setup(e){const t=En(),n=T(null),o=H(()=>e.show),r=T(e.defaultShow),a=Et(o,r),l=Ue(()=>e.disabled?!1:a.value),i=()=>{if(e.disabled)return!0;const{getDisabled:E}=e;return!!(E!=null&&E())},s=()=>i()?!1:a.value,c=Fo(e,["arrow","showArrow"]),f=H(()=>e.overlap?!1:c.value);let u=null;const p=T(null),y=T(null),h=Ue(()=>e.x!==void 0&&e.y!==void 0);function b(E){const{"onUpdate:show":J,onUpdateShow:Q,onShow:X,onHide:te}=e;r.value=E,J&&ge(J,E),Q&&ge(Q,E),E&&X&&ge(X,!0),E&&te&&ge(te,!1)}function w(){u&&u.syncPosition()}function m(){const{value:E}=p;E&&(window.clearTimeout(E),p.value=null)}function B(){const{value:E}=y;E&&(window.clearTimeout(E),y.value=null)}function W(){const E=i();if(e.trigger==="focus"&&!E){if(s())return;b(!0)}}function F(){const E=i();if(e.trigger==="focus"&&!E){if(!s())return;b(!1)}}function C(){const E=i();if(e.trigger==="hover"&&!E){if(B(),p.value!==null||s())return;const J=()=>{b(!0),p.value=null},{delay:Q}=e;Q===0?J():p.value=window.setTimeout(J,Q)}}function P(){const E=i();if(e.trigger==="hover"&&!E){if(m(),y.value!==null||!s())return;const J=()=>{b(!1),y.value=null},{duration:Q}=e;Q===0?J():y.value=window.setTimeout(J,Q)}}function V(){P()}function S(E){var J;s()&&(e.trigger==="click"&&(m(),B(),b(!1)),(J=e.onClickoutside)===null||J===void 0||J.call(e,E))}function k(){if(e.trigger==="click"&&!i()){m(),B();const E=!s();b(E)}}function R(E){e.internalTrapFocus&&E.key==="Escape"&&(m(),B(),b(!1))}function K(E){r.value=E}function j(){var E;return(E=n.value)===null||E===void 0?void 0:E.targetRef}function z(E){u=E}return Ge("NPopover",{getTriggerElement:j,handleKeydown:R,handleMouseEnter:C,handleMouseLeave:P,handleClickOutside:S,handleMouseMoveOutside:V,setBodyInstance:z,positionManuallyRef:h,isMountedRef:t,zIndexRef:_e(e,"zIndex"),extraClassRef:_e(e,"internalExtraClass"),internalRenderBodyRef:_e(e,"internalRenderBody")}),Bt(()=>{a.value&&i()&&b(!1)}),{binderInstRef:n,positionManually:h,mergedShowConsideringDisabledProp:l,uncontrolledShow:r,mergedShowArrow:f,getMergedShow:s,setShow:K,handleClick:k,handleMouseEnter:C,handleMouseLeave:P,handleFocus:W,handleBlur:F,syncPosition:w}},render(){var e;const{positionManually:t,$slots:n}=this;let o,r=!1;if(!t&&(o=El(n,"trigger"),o)){o=za(o),o=o.type===Pa?d("span",[o]):o;const a={onClick:this.handleClick,onMouseenter:this.handleMouseEnter,onMouseleave:this.handleMouseLeave,onFocus:this.handleFocus,onBlur:this.handleBlur};if(!((e=o.type)===null||e===void 0)&&e.__popover__)r=!0,o.props||(o.props={internalSyncTargetWithParent:!0,internalInheritedEventHandlers:[]}),o.props.internalSyncTargetWithParent=!0,o.props.internalInheritedEventHandlers?o.props.internalInheritedEventHandlers=[a,...o.props.internalInheritedEventHandlers]:o.props.internalInheritedEventHandlers=[a];else{const{internalInheritedEventHandlers:l}=this,i=[a,...l],s={onBlur:c=>{i.forEach(f=>{f.onBlur(c)})},onFocus:c=>{i.forEach(f=>{f.onFocus(c)})},onClick:c=>{i.forEach(f=>{f.onClick(c)})},onMouseenter:c=>{i.forEach(f=>{f.onMouseenter(c)})},onMouseleave:c=>{i.forEach(f=>{f.onMouseleave(c)})}};Mc(o,l?"nested":t?"manual":this.trigger,s)}}return d(Xr,{ref:"binderInstRef",syncTarget:!r,syncTargetWithParent:this.internalSyncTargetWithParent},{default:()=>{this.mergedShowConsideringDisabledProp;const a=this.getMergedShow();return[this.internalTrapFocus&&a?_t(d("div",{style:{position:"fixed",top:0,right:0,bottom:0,left:0}}),[[Do,{enabled:a,zIndex:this.zIndex}]]):null,t?null:d(Yr,null,{default:()=>o}),d($c,Ma(this.$props,zc,Object.assign(Object.assign({},this.$attrs),{showArrow:this.mergedShowArrow,show:a})),{default:()=>{var l,i;return(i=(l=this.$slots).default)===null||i===void 0?void 0:i.call(l)},header:()=>{var l,i;return(i=(l=this.$slots).header)===null||i===void 0?void 0:i.call(l)},footer:()=>{var l,i;return(i=(l=this.$slots).footer)===null||i===void 0?void 0:i.call(l)}})]}})}}),Bc={color:Object,type:{type:String,default:"default"},round:Boolean,size:String,closable:Boolean,disabled:{type:Boolean,default:void 0}},Ec=N("tag",`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[Z("strong",`
 font-weight: var(--n-font-weight-strong);
 `),_("border",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),_("icon",`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),_("avatar",`
 display: flex;
 margin: 0 6px 0 0;
 `),_("close",`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),Z("round",`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[_("icon",`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),_("avatar",`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),Z("closable",`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),Z("icon, avatar",[Z("round",`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),Z("disabled",`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),Z("checkable",`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[De("disabled",[D("&:hover","background-color: var(--n-color-hover-checkable);",[De("checked","color: var(--n-text-color-hover-checkable);")]),D("&:active","background-color: var(--n-color-pressed-checkable);",[De("checked","color: var(--n-text-color-pressed-checkable);")])]),Z("checked",`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[De("disabled",[D("&:hover","background-color: var(--n-color-checked-hover);"),D("&:active","background-color: var(--n-color-checked-pressed);")])])])]),Ic=Object.assign(Object.assign(Object.assign({},Be.props),Bc),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),Rc=ut("n-tag"),uo=Se({name:"Tag",props:Ic,slots:Object,setup(e){const t=T(null),{mergedBorderedRef:n,mergedClsPrefixRef:o,inlineThemeDisabled:r,mergedRtlRef:a,mergedComponentPropsRef:l}=ot(e),i=H(()=>{var b,w;return e.size||((w=(b=l==null?void 0:l.value)===null||b===void 0?void 0:b.Tag)===null||w===void 0?void 0:w.size)||"medium"}),s=Be("Tag","-tag",Ec,Ta,e,o);Ge(Rc,{roundRef:_e(e,"round")});function c(){if(!e.disabled&&e.checkable){const{checked:b,onCheckedChange:w,onUpdateChecked:m,"onUpdate:checked":B}=e;m&&m(!b),B&&B(!b),w&&w(!b)}}function f(b){if(e.triggerClickOnClose||b.stopPropagation(),!e.disabled){const{onClose:w}=e;w&&ge(w,b)}}const u={setTextContent(b){const{value:w}=t;w&&(w.textContent=b)}},p=It("Tag",a,o),y=H(()=>{const{type:b,color:{color:w,textColor:m}={}}=e,B=i.value,{common:{cubicBezierEaseInOut:W},self:{padding:F,closeMargin:C,borderRadius:P,opacityDisabled:V,textColorCheckable:S,textColorHoverCheckable:k,textColorPressedCheckable:R,textColorChecked:K,colorCheckable:j,colorHoverCheckable:z,colorPressedCheckable:G,colorChecked:E,colorCheckedHover:J,colorCheckedPressed:Q,closeBorderRadius:X,fontWeightStrong:te,[q("colorBordered",b)]:ue,[q("closeSize",B)]:le,[q("closeIconSize",B)]:re,[q("fontSize",B)]:xe,[q("height",B)]:O,[q("color",b)]:L,[q("textColor",b)]:pe,[q("border",b)]:fe,[q("closeIconColor",b)]:Me,[q("closeIconColorHover",b)]:Fe,[q("closeIconColorPressed",b)]:ie,[q("closeColorHover",b)]:Ne,[q("closeColorPressed",b)]:Le}}=s.value,Ve=Ot(C);return{"--n-font-weight-strong":te,"--n-avatar-size-override":`calc(${O} - 8px)`,"--n-bezier":W,"--n-border-radius":P,"--n-border":fe,"--n-close-icon-size":re,"--n-close-color-pressed":Le,"--n-close-color-hover":Ne,"--n-close-border-radius":X,"--n-close-icon-color":Me,"--n-close-icon-color-hover":Fe,"--n-close-icon-color-pressed":ie,"--n-close-icon-color-disabled":Me,"--n-close-margin-top":Ve.top,"--n-close-margin-right":Ve.right,"--n-close-margin-bottom":Ve.bottom,"--n-close-margin-left":Ve.left,"--n-close-size":le,"--n-color":w||(n.value?ue:L),"--n-color-checkable":j,"--n-color-checked":E,"--n-color-checked-hover":J,"--n-color-checked-pressed":Q,"--n-color-hover-checkable":z,"--n-color-pressed-checkable":G,"--n-font-size":xe,"--n-height":O,"--n-opacity-disabled":V,"--n-padding":F,"--n-text-color":m||pe,"--n-text-color-checkable":S,"--n-text-color-checked":K,"--n-text-color-hover-checkable":k,"--n-text-color-pressed-checkable":R}}),h=r?at("tag",H(()=>{let b="";const{type:w,color:{color:m,textColor:B}={}}=e;return b+=w[0],b+=i.value[0],m&&(b+=`a${Tn(m)}`),B&&(b+=`b${Tn(B)}`),n.value&&(b+="c"),b}),y,e):void 0;return Object.assign(Object.assign({},u),{rtlEnabled:p,mergedClsPrefix:o,contentRef:t,mergedBordered:n,handleClick:c,handleCloseClick:f,cssVars:r?void 0:y,themeClass:h==null?void 0:h.themeClass,onRender:h==null?void 0:h.onRender})},render(){var e,t;const{mergedClsPrefix:n,rtlEnabled:o,closable:r,color:{borderColor:a}={},round:l,onRender:i,$slots:s}=this;i==null||i();const c=Re(s.avatar,u=>u&&d("div",{class:`${n}-tag__avatar`},u)),f=Re(s.icon,u=>u&&d("div",{class:`${n}-tag__icon`},u));return d("div",{class:[`${n}-tag`,this.themeClass,{[`${n}-tag--rtl`]:o,[`${n}-tag--strong`]:this.strong,[`${n}-tag--disabled`]:this.disabled,[`${n}-tag--checkable`]:this.checkable,[`${n}-tag--checked`]:this.checkable&&this.checked,[`${n}-tag--round`]:l,[`${n}-tag--avatar`]:c,[`${n}-tag--icon`]:f,[`${n}-tag--closable`]:r}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},f||c,d("span",{class:`${n}-tag__content`,ref:"contentRef"},(t=(e=this.$slots).default)===null||t===void 0?void 0:t.call(e)),!this.checkable&&r?d(Lr,{clsPrefix:n,class:`${n}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:l,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?d("div",{class:`${n}-tag__border`,style:{borderColor:a}}):null)}}),pi=Se({name:"InternalSelectionSuffix",props:{clsPrefix:{type:String,required:!0},showArrow:{type:Boolean,default:void 0},showClear:{type:Boolean,default:void 0},loading:{type:Boolean,default:!1},onClear:Function},setup(e,{slots:t}){return()=>{const{clsPrefix:n}=e;return d(vn,{clsPrefix:n,class:`${n}-base-suffix`,strokeWidth:24,scale:.85,show:e.loading},{default:()=>e.showArrow?d(Co,{clsPrefix:n,show:e.showClear,onClear:e.onClear},{placeholder:()=>d(Zt,{clsPrefix:n,class:`${n}-base-suffix__arrow`},{default:()=>Yt(t.default,()=>[d(Wd,null)])})}):null})}}}),Ac=D([N("base-selection",`
 --n-padding-single: var(--n-padding-single-top) var(--n-padding-single-right) var(--n-padding-single-bottom) var(--n-padding-single-left);
 --n-padding-multiple: var(--n-padding-multiple-top) var(--n-padding-multiple-right) var(--n-padding-multiple-bottom) var(--n-padding-multiple-left);
 position: relative;
 z-index: auto;
 box-shadow: none;
 width: 100%;
 max-width: 100%;
 display: inline-block;
 vertical-align: bottom;
 border-radius: var(--n-border-radius);
 min-height: var(--n-height);
 line-height: 1.5;
 font-size: var(--n-font-size);
 `,[N("base-loading",`
 color: var(--n-loading-color);
 `),N("base-selection-tags","min-height: var(--n-height);"),_("border, state-border",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 border: var(--n-border);
 border-radius: inherit;
 transition:
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `),_("state-border",`
 z-index: 1;
 border-color: #0000;
 `),N("base-suffix",`
 cursor: pointer;
 position: absolute;
 top: 50%;
 transform: translateY(-50%);
 right: 10px;
 `,[_("arrow",`
 font-size: var(--n-arrow-size);
 color: var(--n-arrow-color);
 transition: color .3s var(--n-bezier);
 `)]),N("base-selection-overlay",`
 display: flex;
 align-items: center;
 white-space: nowrap;
 pointer-events: none;
 position: absolute;
 top: 0;
 right: 0;
 bottom: 0;
 left: 0;
 padding: var(--n-padding-single);
 transition: color .3s var(--n-bezier);
 `,[_("wrapper",`
 flex-basis: 0;
 flex-grow: 1;
 overflow: hidden;
 text-overflow: ellipsis;
 `)]),N("base-selection-placeholder",`
 color: var(--n-placeholder-color);
 `,[_("inner",`
 max-width: 100%;
 overflow: hidden;
 `)]),N("base-selection-tags",`
 cursor: pointer;
 outline: none;
 box-sizing: border-box;
 position: relative;
 z-index: auto;
 display: flex;
 padding: var(--n-padding-multiple);
 flex-wrap: wrap;
 align-items: center;
 width: 100%;
 vertical-align: bottom;
 background-color: var(--n-color);
 border-radius: inherit;
 transition:
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `),N("base-selection-label",`
 height: var(--n-height);
 display: inline-flex;
 width: 100%;
 vertical-align: bottom;
 cursor: pointer;
 outline: none;
 z-index: auto;
 box-sizing: border-box;
 position: relative;
 transition:
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 border-radius: inherit;
 background-color: var(--n-color);
 align-items: center;
 `,[N("base-selection-input",`
 font-size: inherit;
 line-height: inherit;
 outline: none;
 cursor: pointer;
 box-sizing: border-box;
 border:none;
 width: 100%;
 padding: var(--n-padding-single);
 background-color: #0000;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 caret-color: var(--n-caret-color);
 `,[_("content",`
 text-overflow: ellipsis;
 overflow: hidden;
 white-space: nowrap; 
 `)]),_("render-label",`
 color: var(--n-text-color);
 `)]),De("disabled",[D("&:hover",[_("state-border",`
 box-shadow: var(--n-box-shadow-hover);
 border: var(--n-border-hover);
 `)]),Z("focus",[_("state-border",`
 box-shadow: var(--n-box-shadow-focus);
 border: var(--n-border-focus);
 `)]),Z("active",[_("state-border",`
 box-shadow: var(--n-box-shadow-active);
 border: var(--n-border-active);
 `),N("base-selection-label","background-color: var(--n-color-active);"),N("base-selection-tags","background-color: var(--n-color-active);")])]),Z("disabled","cursor: not-allowed;",[_("arrow",`
 color: var(--n-arrow-color-disabled);
 `),N("base-selection-label",`
 cursor: not-allowed;
 background-color: var(--n-color-disabled);
 `,[N("base-selection-input",`
 cursor: not-allowed;
 color: var(--n-text-color-disabled);
 `),_("render-label",`
 color: var(--n-text-color-disabled);
 `)]),N("base-selection-tags",`
 cursor: not-allowed;
 background-color: var(--n-color-disabled);
 `),N("base-selection-placeholder",`
 cursor: not-allowed;
 color: var(--n-placeholder-color-disabled);
 `)]),N("base-selection-input-tag",`
 height: calc(var(--n-height) - 6px);
 line-height: calc(var(--n-height) - 6px);
 outline: none;
 display: none;
 position: relative;
 margin-bottom: 3px;
 max-width: 100%;
 vertical-align: bottom;
 `,[_("input",`
 font-size: inherit;
 font-family: inherit;
 min-width: 1px;
 padding: 0;
 background-color: #0000;
 outline: none;
 border: none;
 max-width: 100%;
 overflow: hidden;
 width: 1em;
 line-height: inherit;
 cursor: pointer;
 color: var(--n-text-color);
 caret-color: var(--n-caret-color);
 `),_("mirror",`
 position: absolute;
 left: 0;
 top: 0;
 white-space: pre;
 visibility: hidden;
 user-select: none;
 -webkit-user-select: none;
 opacity: 0;
 `)]),["warning","error"].map(e=>Z(`${e}-status`,[_("state-border",`border: var(--n-border-${e});`),De("disabled",[D("&:hover",[_("state-border",`
 box-shadow: var(--n-box-shadow-hover-${e});
 border: var(--n-border-hover-${e});
 `)]),Z("active",[_("state-border",`
 box-shadow: var(--n-box-shadow-active-${e});
 border: var(--n-border-active-${e});
 `),N("base-selection-label",`background-color: var(--n-color-active-${e});`),N("base-selection-tags",`background-color: var(--n-color-active-${e});`)]),Z("focus",[_("state-border",`
 box-shadow: var(--n-box-shadow-focus-${e});
 border: var(--n-border-focus-${e});
 `)])])]))]),N("base-selection-popover",`
 margin-bottom: -3px;
 display: flex;
 flex-wrap: wrap;
 margin-right: -8px;
 `),N("base-selection-tag-wrapper",`
 max-width: 100%;
 display: inline-flex;
 padding: 0 7px 3px 0;
 `,[D("&:last-child","padding-right: 0;"),N("tag",`
 font-size: 14px;
 max-width: 100%;
 `,[_("content",`
 line-height: 1.25;
 text-overflow: ellipsis;
 overflow: hidden;
 `)])])]),Dc=Se({name:"InternalSelection",props:Object.assign(Object.assign({},Be.props),{clsPrefix:{type:String,required:!0},bordered:{type:Boolean,default:void 0},active:Boolean,pattern:{type:String,default:""},placeholder:String,selectedOption:{type:Object,default:null},selectedOptions:{type:Array,default:null},labelField:{type:String,default:"label"},valueField:{type:String,default:"value"},multiple:Boolean,filterable:Boolean,clearable:Boolean,disabled:Boolean,size:{type:String,default:"medium"},loading:Boolean,autofocus:Boolean,showArrow:{type:Boolean,default:!0},inputProps:Object,focused:Boolean,renderTag:Function,onKeydown:Function,onClick:Function,onBlur:Function,onFocus:Function,onDeleteOption:Function,maxTagCount:[String,Number],ellipsisTagPopoverProps:Object,onClear:Function,onPatternInput:Function,onPatternFocus:Function,onPatternBlur:Function,renderLabel:Function,status:String,inlineThemeDisabled:Boolean,ignoreComposition:{type:Boolean,default:!0},onResize:Function}),setup(e){const{mergedClsPrefixRef:t,mergedRtlRef:n}=ot(e),o=It("InternalSelection",n,t),r=T(null),a=T(null),l=T(null),i=T(null),s=T(null),c=T(null),f=T(null),u=T(null),p=T(null),y=T(null),h=T(!1),b=T(!1),w=T(!1),m=Be("InternalSelection","-internal-selection",Ac,Oa,e,_e(e,"clsPrefix")),B=H(()=>e.clearable&&!e.disabled&&(w.value||e.active)),W=H(()=>e.selectedOption?e.renderTag?e.renderTag({option:e.selectedOption,handleClose:()=>{}}):e.renderLabel?e.renderLabel(e.selectedOption,!0):Gt(e.selectedOption[e.labelField],e.selectedOption,!0):e.placeholder),F=H(()=>{const A=e.selectedOption;if(A)return A[e.labelField]}),C=H(()=>e.multiple?!!(Array.isArray(e.selectedOptions)&&e.selectedOptions.length):e.selectedOption!==null);function P(){var A;const{value:Y}=r;if(Y){const{value:Oe}=a;Oe&&(Oe.style.width=`${Y.offsetWidth}px`,e.maxTagCount!=="responsive"&&((A=p.value)===null||A===void 0||A.sync({showAllItemsBeforeCalculate:!1})))}}function V(){const{value:A}=y;A&&(A.style.display="none")}function S(){const{value:A}=y;A&&(A.style.display="inline-block")}Ie(_e(e,"active"),A=>{A||V()}),Ie(_e(e,"pattern"),()=>{e.multiple&&mt(P)});function k(A){const{onFocus:Y}=e;Y&&Y(A)}function R(A){const{onBlur:Y}=e;Y&&Y(A)}function K(A){const{onDeleteOption:Y}=e;Y&&Y(A)}function j(A){const{onClear:Y}=e;Y&&Y(A)}function z(A){const{onPatternInput:Y}=e;Y&&Y(A)}function G(A){var Y;(!A.relatedTarget||!(!((Y=l.value)===null||Y===void 0)&&Y.contains(A.relatedTarget)))&&k(A)}function E(A){var Y;!((Y=l.value)===null||Y===void 0)&&Y.contains(A.relatedTarget)||R(A)}function J(A){j(A)}function Q(){w.value=!0}function X(){w.value=!1}function te(A){!e.active||!e.filterable||A.target!==a.value&&A.preventDefault()}function ue(A){K(A)}const le=T(!1);function re(A){if(A.key==="Backspace"&&!le.value&&!e.pattern.length){const{selectedOptions:Y}=e;Y!=null&&Y.length&&ue(Y[Y.length-1])}}let xe=null;function O(A){const{value:Y}=r;if(Y){const Oe=A.target.value;Y.textContent=Oe,P()}e.ignoreComposition&&le.value?xe=A:z(A)}function L(){le.value=!0}function pe(){le.value=!1,e.ignoreComposition&&z(xe),xe=null}function fe(A){var Y;b.value=!0,(Y=e.onPatternFocus)===null||Y===void 0||Y.call(e,A)}function Me(A){var Y;b.value=!1,(Y=e.onPatternBlur)===null||Y===void 0||Y.call(e,A)}function Fe(){var A,Y;if(e.filterable)b.value=!1,(A=c.value)===null||A===void 0||A.blur(),(Y=a.value)===null||Y===void 0||Y.blur();else if(e.multiple){const{value:Oe}=i;Oe==null||Oe.blur()}else{const{value:Oe}=s;Oe==null||Oe.blur()}}function ie(){var A,Y,Oe;e.filterable?(b.value=!1,(A=c.value)===null||A===void 0||A.focus()):e.multiple?(Y=i.value)===null||Y===void 0||Y.focus():(Oe=s.value)===null||Oe===void 0||Oe.focus()}function Ne(){const{value:A}=a;A&&(S(),A.focus())}function Le(){const{value:A}=a;A&&A.blur()}function Ve(A){const{value:Y}=f;Y&&Y.setTextContent(`+${A}`)}function rt(){const{value:A}=u;return A}function it(){return a.value}let Ke=null;function Xe(){Ke!==null&&window.clearTimeout(Ke)}function I(){e.active||(Xe(),Ke=window.setTimeout(()=>{C.value&&(h.value=!0)},100))}function g(){Xe()}function ce(A){A||(Xe(),h.value=!1)}Ie(C,A=>{A||(h.value=!1)}),nt(()=>{Bt(()=>{const A=c.value;A&&(e.disabled?A.removeAttribute("tabindex"):A.tabIndex=b.value?-1:0)})}),ii(l,e.onResize);const{inlineThemeDisabled:ee}=e,ne=H(()=>{const{size:A}=e,{common:{cubicBezierEaseInOut:Y},self:{fontWeight:Oe,borderRadius:he,color:me,placeholderColor:He,textColor:be,paddingSingle:lt,paddingMultiple:st,caretColor:tn,colorDisabled:nn,textColorDisabled:Rt,placeholderColorDisabled:dt,colorActive:x,boxShadowFocus:U,boxShadowActive:ae,boxShadowHover:we,border:ve,borderFocus:ye,borderHover:Ce,borderActive:Ee,arrowColor:Ye,arrowColorDisabled:Wn,loadingColor:bn,colorActiveWarning:Nn,boxShadowFocusWarning:At,boxShadowActiveWarning:Dt,boxShadowHoverWarning:Vn,borderWarning:Hn,borderFocusWarning:mn,borderHoverWarning:wt,borderActiveWarning:v,colorActiveError:M,boxShadowFocusError:oe,boxShadowActiveError:ze,boxShadowHoverError:Pe,borderError:$e,borderFocusError:ft,borderHoverError:ht,borderActiveError:vt,clearColor:zt,clearColorHover:Pt,clearColorPressed:on,clearSize:jn,arrowSize:Kn,[q("height",A)]:Un,[q("fontSize",A)]:Gn}}=m.value,Lt=Ot(lt),Wt=Ot(st);return{"--n-bezier":Y,"--n-border":ve,"--n-border-active":Ee,"--n-border-focus":ye,"--n-border-hover":Ce,"--n-border-radius":he,"--n-box-shadow-active":ae,"--n-box-shadow-focus":U,"--n-box-shadow-hover":we,"--n-caret-color":tn,"--n-color":me,"--n-color-active":x,"--n-color-disabled":nn,"--n-font-size":Gn,"--n-height":Un,"--n-padding-single-top":Lt.top,"--n-padding-multiple-top":Wt.top,"--n-padding-single-right":Lt.right,"--n-padding-multiple-right":Wt.right,"--n-padding-single-left":Lt.left,"--n-padding-multiple-left":Wt.left,"--n-padding-single-bottom":Lt.bottom,"--n-padding-multiple-bottom":Wt.bottom,"--n-placeholder-color":He,"--n-placeholder-color-disabled":dt,"--n-text-color":be,"--n-text-color-disabled":Rt,"--n-arrow-color":Ye,"--n-arrow-color-disabled":Wn,"--n-loading-color":bn,"--n-color-active-warning":Nn,"--n-box-shadow-focus-warning":At,"--n-box-shadow-active-warning":Dt,"--n-box-shadow-hover-warning":Vn,"--n-border-warning":Hn,"--n-border-focus-warning":mn,"--n-border-hover-warning":wt,"--n-border-active-warning":v,"--n-color-active-error":M,"--n-box-shadow-focus-error":oe,"--n-box-shadow-active-error":ze,"--n-box-shadow-hover-error":Pe,"--n-border-error":$e,"--n-border-focus-error":ft,"--n-border-hover-error":ht,"--n-border-active-error":vt,"--n-clear-size":jn,"--n-clear-color":zt,"--n-clear-color-hover":Pt,"--n-clear-color-pressed":on,"--n-arrow-size":Kn,"--n-font-weight":Oe}}),ke=ee?at("internal-selection",H(()=>e.size[0]),ne,e):void 0;return{mergedTheme:m,mergedClearable:B,mergedClsPrefix:t,rtlEnabled:o,patternInputFocused:b,filterablePlaceholder:W,label:F,selected:C,showTagsPanel:h,isComposing:le,counterRef:f,counterWrapperRef:u,patternInputMirrorRef:r,patternInputRef:a,selfRef:l,multipleElRef:i,singleElRef:s,patternInputWrapperRef:c,overflowRef:p,inputTagElRef:y,handleMouseDown:te,handleFocusin:G,handleClear:J,handleMouseEnter:Q,handleMouseLeave:X,handleDeleteOption:ue,handlePatternKeyDown:re,handlePatternInputInput:O,handlePatternInputBlur:Me,handlePatternInputFocus:fe,handleMouseEnterCounter:I,handleMouseLeaveCounter:g,handleFocusout:E,handleCompositionEnd:pe,handleCompositionStart:L,onPopoverUpdateShow:ce,focus:ie,focusInput:Ne,blur:Fe,blurInput:Le,updateCounter:Ve,getCounter:rt,getTail:it,renderLabel:e.renderLabel,cssVars:ee?void 0:ne,themeClass:ke==null?void 0:ke.themeClass,onRender:ke==null?void 0:ke.onRender}},render(){const{status:e,multiple:t,size:n,disabled:o,filterable:r,maxTagCount:a,bordered:l,clsPrefix:i,ellipsisTagPopoverProps:s,onRender:c,renderTag:f,renderLabel:u}=this;c==null||c();const p=a==="responsive",y=typeof a=="number",h=p||y,b=d(Fa,null,{default:()=>d(pi,{clsPrefix:i,loading:this.loading,showArrow:this.showArrow,showClear:this.mergedClearable&&this.selected,onClear:this.handleClear},{default:()=>{var m,B;return(B=(m=this.$slots).arrow)===null||B===void 0?void 0:B.call(m)}})});let w;if(t){const{labelField:m}=this,B=z=>d("div",{class:`${i}-base-selection-tag-wrapper`,key:z.value},f?f({option:z,handleClose:()=>{this.handleDeleteOption(z)}}):d(uo,{size:n,closable:!z.disabled,disabled:o,onClose:()=>{this.handleDeleteOption(z)},internalCloseIsButtonTag:!1,internalCloseFocusable:!1},{default:()=>u?u(z,!0):Gt(z[m],z,!0)})),W=()=>(y?this.selectedOptions.slice(0,a):this.selectedOptions).map(B),F=r?d("div",{class:`${i}-base-selection-input-tag`,ref:"inputTagElRef",key:"__input-tag__"},d("input",Object.assign({},this.inputProps,{ref:"patternInputRef",tabindex:-1,disabled:o,value:this.pattern,autofocus:this.autofocus,class:`${i}-base-selection-input-tag__input`,onBlur:this.handlePatternInputBlur,onFocus:this.handlePatternInputFocus,onKeydown:this.handlePatternKeyDown,onInput:this.handlePatternInputInput,onCompositionstart:this.handleCompositionStart,onCompositionend:this.handleCompositionEnd})),d("span",{ref:"patternInputMirrorRef",class:`${i}-base-selection-input-tag__mirror`},this.pattern)):null,C=p?()=>d("div",{class:`${i}-base-selection-tag-wrapper`,ref:"counterWrapperRef"},d(uo,{size:n,ref:"counterRef",onMouseenter:this.handleMouseEnterCounter,onMouseleave:this.handleMouseLeaveCounter,disabled:o})):void 0;let P;if(y){const z=this.selectedOptions.length-a;z>0&&(P=d("div",{class:`${i}-base-selection-tag-wrapper`,key:"__counter__"},d(uo,{size:n,ref:"counterRef",onMouseenter:this.handleMouseEnterCounter,disabled:o},{default:()=>`+${z}`})))}const V=p?r?d(vr,{ref:"overflowRef",updateCounter:this.updateCounter,getCounter:this.getCounter,getTail:this.getTail,style:{width:"100%",display:"flex",overflow:"hidden"}},{default:W,counter:C,tail:()=>F}):d(vr,{ref:"overflowRef",updateCounter:this.updateCounter,getCounter:this.getCounter,style:{width:"100%",display:"flex",overflow:"hidden"}},{default:W,counter:C}):y&&P?W().concat(P):W(),S=h?()=>d("div",{class:`${i}-base-selection-popover`},p?W():this.selectedOptions.map(B)):void 0,k=h?Object.assign({show:this.showTagsPanel,trigger:"hover",overlap:!0,placement:"top",width:"trigger",onUpdateShow:this.onPopoverUpdateShow,theme:this.mergedTheme.peers.Popover,themeOverrides:this.mergedTheme.peerOverrides.Popover},s):null,K=(this.selected?!1:this.active?!this.pattern&&!this.isComposing:!0)?d("div",{class:`${i}-base-selection-placeholder ${i}-base-selection-overlay`},d("div",{class:`${i}-base-selection-placeholder__inner`},this.placeholder)):null,j=r?d("div",{ref:"patternInputWrapperRef",class:`${i}-base-selection-tags`},V,p?null:F,b):d("div",{ref:"multipleElRef",class:`${i}-base-selection-tags`,tabindex:o?void 0:0},V,b);w=d(je,null,h?d(Oc,Object.assign({},k,{scrollable:!0,style:"max-height: calc(var(--v-target-height) * 6.6);"}),{trigger:()=>j,default:S}):j,K)}else if(r){const m=this.pattern||this.isComposing,B=this.active?!m:!this.selected,W=this.active?!1:this.selected;w=d("div",{ref:"patternInputWrapperRef",class:`${i}-base-selection-label`,title:this.patternInputFocused?void 0:pr(this.label)},d("input",Object.assign({},this.inputProps,{ref:"patternInputRef",class:`${i}-base-selection-input`,value:this.active?this.pattern:"",placeholder:"",readonly:o,disabled:o,tabindex:-1,autofocus:this.autofocus,onFocus:this.handlePatternInputFocus,onBlur:this.handlePatternInputBlur,onInput:this.handlePatternInputInput,onCompositionstart:this.handleCompositionStart,onCompositionend:this.handleCompositionEnd})),W?d("div",{class:`${i}-base-selection-label__render-label ${i}-base-selection-overlay`,key:"input"},d("div",{class:`${i}-base-selection-overlay__wrapper`},f?f({option:this.selectedOption,handleClose:()=>{}}):u?u(this.selectedOption,!0):Gt(this.label,this.selectedOption,!0))):null,B?d("div",{class:`${i}-base-selection-placeholder ${i}-base-selection-overlay`,key:"placeholder"},d("div",{class:`${i}-base-selection-overlay__wrapper`},this.filterablePlaceholder)):null,b)}else w=d("div",{ref:"singleElRef",class:`${i}-base-selection-label`,tabindex:this.disabled?void 0:0},this.label!==void 0?d("div",{class:`${i}-base-selection-input`,title:pr(this.label),key:"input"},d("div",{class:`${i}-base-selection-input__content`},f?f({option:this.selectedOption,handleClose:()=>{}}):u?u(this.selectedOption,!0):Gt(this.label,this.selectedOption,!0))):d("div",{class:`${i}-base-selection-placeholder ${i}-base-selection-overlay`,key:"placeholder"},d("div",{class:`${i}-base-selection-placeholder__inner`},this.placeholder)),b);return d("div",{ref:"selfRef",class:[`${i}-base-selection`,this.rtlEnabled&&`${i}-base-selection--rtl`,this.themeClass,e&&`${i}-base-selection--${e}-status`,{[`${i}-base-selection--active`]:this.active,[`${i}-base-selection--selected`]:this.selected||this.active&&this.pattern,[`${i}-base-selection--disabled`]:this.disabled,[`${i}-base-selection--multiple`]:this.multiple,[`${i}-base-selection--focus`]:this.focused}],style:this.cssVars,onClick:this.onClick,onMouseenter:this.handleMouseEnter,onMouseleave:this.handleMouseLeave,onKeydown:this.onKeydown,onFocusin:this.handleFocusin,onFocusout:this.handleFocusout,onMousedown:this.handleMouseDown},w,l?d("div",{class:`${i}-base-selection__border`}):null,l?d("div",{class:`${i}-base-selection__state-border`}):null)}}),{cubicBezierEaseInOut:Ct}=en;function Lc({duration:e=".2s",delay:t=".1s"}={}){return[D("&.fade-in-width-expand-transition-leave-from, &.fade-in-width-expand-transition-enter-to",{opacity:1}),D("&.fade-in-width-expand-transition-leave-to, &.fade-in-width-expand-transition-enter-from",`
 opacity: 0!important;
 margin-left: 0!important;
 margin-right: 0!important;
 `),D("&.fade-in-width-expand-transition-leave-active",`
 overflow: hidden;
 transition:
 opacity ${e} ${Ct},
 max-width ${e} ${Ct} ${t},
 margin-left ${e} ${Ct} ${t},
 margin-right ${e} ${Ct} ${t};
 `),D("&.fade-in-width-expand-transition-enter-active",`
 overflow: hidden;
 transition:
 opacity ${e} ${Ct} ${t},
 max-width ${e} ${Ct},
 margin-left ${e} ${Ct},
 margin-right ${e} ${Ct};
 `)]}const Wc=N("base-wave",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
`),Nc=Se({name:"BaseWave",props:{clsPrefix:{type:String,required:!0}},setup(e){To("-base-wave",Wc,_e(e,"clsPrefix"));const t=T(null),n=T(!1);let o=null;return Je(()=>{o!==null&&window.clearTimeout(o)}),{active:n,selfRef:t,play(){o!==null&&(window.clearTimeout(o),n.value=!1,o=null),mt(()=>{var r;(r=t.value)===null||r===void 0||r.offsetHeight,n.value=!0,o=window.setTimeout(()=>{n.value=!1,o=null},1e3)})}}},render(){const{clsPrefix:e}=this;return d("div",{ref:"selfRef","aria-hidden":!0,class:[`${e}-base-wave`,this.active&&`${e}-base-wave--active`]})}}),Vc=gn&&"chrome"in window;gn&&navigator.userAgent.includes("Firefox");const bi=gn&&navigator.userAgent.includes("Safari")&&!Vc,mi=ut("n-input"),Hc=N("input",`
 max-width: 100%;
 cursor: text;
 line-height: 1.5;
 z-index: auto;
 outline: none;
 box-sizing: border-box;
 position: relative;
 display: inline-flex;
 border-radius: var(--n-border-radius);
 background-color: var(--n-color);
 transition: background-color .3s var(--n-bezier);
 font-size: var(--n-font-size);
 font-weight: var(--n-font-weight);
 --n-padding-vertical: calc((var(--n-height) - 1.5 * var(--n-font-size)) / 2);
`,[_("input, textarea",`
 overflow: hidden;
 flex-grow: 1;
 position: relative;
 `),_("input-el, textarea-el, input-mirror, textarea-mirror, separator, placeholder",`
 box-sizing: border-box;
 font-size: inherit;
 line-height: 1.5;
 font-family: inherit;
 border: none;
 outline: none;
 background-color: #0000;
 text-align: inherit;
 transition:
 -webkit-text-fill-color .3s var(--n-bezier),
 caret-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 text-decoration-color .3s var(--n-bezier);
 `),_("input-el, textarea-el",`
 -webkit-appearance: none;
 scrollbar-width: none;
 width: 100%;
 min-width: 0;
 text-decoration-color: var(--n-text-decoration-color);
 color: var(--n-text-color);
 caret-color: var(--n-caret-color);
 background-color: transparent;
 `,[D("&::-webkit-scrollbar, &::-webkit-scrollbar-track-piece, &::-webkit-scrollbar-thumb",`
 width: 0;
 height: 0;
 display: none;
 `),D("&::placeholder",`
 color: #0000;
 -webkit-text-fill-color: transparent !important;
 `),D("&:-webkit-autofill ~",[_("placeholder","display: none;")])]),Z("round",[De("textarea","border-radius: calc(var(--n-height) / 2);")]),_("placeholder",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 overflow: hidden;
 color: var(--n-placeholder-color);
 `,[D("span",`
 width: 100%;
 display: inline-block;
 `)]),Z("textarea",[_("placeholder","overflow: visible;")]),De("autosize","width: 100%;"),Z("autosize",[_("textarea-el, input-el",`
 position: absolute;
 top: 0;
 left: 0;
 height: 100%;
 `)]),N("input-wrapper",`
 overflow: hidden;
 display: inline-flex;
 flex-grow: 1;
 position: relative;
 padding-left: var(--n-padding-left);
 padding-right: var(--n-padding-right);
 `),_("input-mirror",`
 padding: 0;
 height: var(--n-height);
 line-height: var(--n-height);
 overflow: hidden;
 visibility: hidden;
 position: static;
 white-space: pre;
 pointer-events: none;
 `),_("input-el",`
 padding: 0;
 height: var(--n-height);
 line-height: var(--n-height);
 `,[D("&[type=password]::-ms-reveal","display: none;"),D("+",[_("placeholder",`
 display: flex;
 align-items: center; 
 `)])]),De("textarea",[_("placeholder","white-space: nowrap;")]),_("eye",`
 display: flex;
 align-items: center;
 justify-content: center;
 transition: color .3s var(--n-bezier);
 `),Z("textarea","width: 100%;",[N("input-word-count",`
 position: absolute;
 right: var(--n-padding-right);
 bottom: var(--n-padding-vertical);
 `),Z("resizable",[N("input-wrapper",`
 resize: vertical;
 min-height: var(--n-height);
 `)]),_("textarea-el, textarea-mirror, placeholder",`
 height: 100%;
 padding-left: 0;
 padding-right: 0;
 padding-top: var(--n-padding-vertical);
 padding-bottom: var(--n-padding-vertical);
 word-break: break-word;
 display: inline-block;
 vertical-align: bottom;
 box-sizing: border-box;
 line-height: var(--n-line-height-textarea);
 margin: 0;
 resize: none;
 white-space: pre-wrap;
 scroll-padding-block-end: var(--n-padding-vertical);
 `),_("textarea-mirror",`
 width: 100%;
 pointer-events: none;
 overflow: hidden;
 visibility: hidden;
 position: static;
 white-space: pre-wrap;
 overflow-wrap: break-word;
 `)]),Z("pair",[_("input-el, placeholder","text-align: center;"),_("separator",`
 display: flex;
 align-items: center;
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 white-space: nowrap;
 `,[N("icon",`
 color: var(--n-icon-color);
 `),N("base-icon",`
 color: var(--n-icon-color);
 `)])]),Z("disabled",`
 cursor: not-allowed;
 background-color: var(--n-color-disabled);
 `,[_("border","border: var(--n-border-disabled);"),_("input-el, textarea-el",`
 cursor: not-allowed;
 color: var(--n-text-color-disabled);
 text-decoration-color: var(--n-text-color-disabled);
 `),_("placeholder","color: var(--n-placeholder-color-disabled);"),_("separator","color: var(--n-text-color-disabled);",[N("icon",`
 color: var(--n-icon-color-disabled);
 `),N("base-icon",`
 color: var(--n-icon-color-disabled);
 `)]),N("input-word-count",`
 color: var(--n-count-text-color-disabled);
 `),_("suffix, prefix","color: var(--n-text-color-disabled);",[N("icon",`
 color: var(--n-icon-color-disabled);
 `),N("internal-icon",`
 color: var(--n-icon-color-disabled);
 `)])]),De("disabled",[_("eye",`
 color: var(--n-icon-color);
 cursor: pointer;
 `,[D("&:hover",`
 color: var(--n-icon-color-hover);
 `),D("&:active",`
 color: var(--n-icon-color-pressed);
 `)]),D("&:hover",[_("state-border","border: var(--n-border-hover);")]),Z("focus","background-color: var(--n-color-focus);",[_("state-border",`
 border: var(--n-border-focus);
 box-shadow: var(--n-box-shadow-focus);
 `)])]),_("border, state-border",`
 box-sizing: border-box;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 border-radius: inherit;
 border: var(--n-border);
 transition:
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `),_("state-border",`
 border-color: #0000;
 z-index: 1;
 `),_("prefix","margin-right: 4px;"),_("suffix",`
 margin-left: 4px;
 `),_("suffix, prefix",`
 transition: color .3s var(--n-bezier);
 flex-wrap: nowrap;
 flex-shrink: 0;
 line-height: var(--n-height);
 white-space: nowrap;
 display: inline-flex;
 align-items: center;
 justify-content: center;
 color: var(--n-suffix-text-color);
 `,[N("base-loading",`
 font-size: var(--n-icon-size);
 margin: 0 2px;
 color: var(--n-loading-color);
 `),N("base-clear",`
 font-size: var(--n-icon-size);
 `,[_("placeholder",[N("base-icon",`
 transition: color .3s var(--n-bezier);
 color: var(--n-icon-color);
 font-size: var(--n-icon-size);
 `)])]),D(">",[N("icon",`
 transition: color .3s var(--n-bezier);
 color: var(--n-icon-color);
 font-size: var(--n-icon-size);
 `)]),N("base-icon",`
 font-size: var(--n-icon-size);
 `)]),N("input-word-count",`
 pointer-events: none;
 line-height: 1.5;
 font-size: .85em;
 color: var(--n-count-text-color);
 transition: color .3s var(--n-bezier);
 margin-left: 4px;
 font-variant: tabular-nums;
 `),["warning","error"].map(e=>Z(`${e}-status`,[De("disabled",[N("base-loading",`
 color: var(--n-loading-color-${e})
 `),_("input-el, textarea-el",`
 caret-color: var(--n-caret-color-${e});
 `),_("state-border",`
 border: var(--n-border-${e});
 `),D("&:hover",[_("state-border",`
 border: var(--n-border-hover-${e});
 `)]),D("&:focus",`
 background-color: var(--n-color-focus-${e});
 `,[_("state-border",`
 box-shadow: var(--n-box-shadow-focus-${e});
 border: var(--n-border-focus-${e});
 `)]),Z("focus",`
 background-color: var(--n-color-focus-${e});
 `,[_("state-border",`
 box-shadow: var(--n-box-shadow-focus-${e});
 border: var(--n-border-focus-${e});
 `)])])]))]),jc=N("input",[Z("disabled",[_("input-el, textarea-el",`
 -webkit-text-fill-color: var(--n-text-color-disabled);
 `)])]);function Kc(e){let t=0;for(const n of e)t++;return t}function Sn(e){return e===""||e==null}function Uc(e){const t=T(null);function n(){const{value:a}=e;if(!(a!=null&&a.focus)){r();return}const{selectionStart:l,selectionEnd:i,value:s}=a;if(l==null||i==null){r();return}t.value={start:l,end:i,beforeText:s.slice(0,l),afterText:s.slice(i)}}function o(){var a;const{value:l}=t,{value:i}=e;if(!l||!i)return;const{value:s}=i,{start:c,beforeText:f,afterText:u}=l;let p=s.length;if(s.endsWith(u))p=s.length-u.length;else if(s.startsWith(f))p=f.length;else{const y=f[c-1],h=s.indexOf(y,c-1);h!==-1&&(p=h+1)}(a=i.setSelectionRange)===null||a===void 0||a.call(i,p,p)}function r(){t.value=null}return Ie(e,r),{recordCursor:n,restoreCursor:o}}const Ir=Se({name:"InputWordCount",setup(e,{slots:t}){const{mergedValueRef:n,maxlengthRef:o,mergedClsPrefixRef:r,countGraphemesRef:a}=We(mi),l=H(()=>{const{value:i}=n;return i===null||Array.isArray(i)?0:(a.value||Kc)(i)});return()=>{const{value:i}=o,{value:s}=n;return d("span",{class:`${r.value}-input-word-count`},Il(t.default,{value:s===null||Array.isArray(s)?"":s},()=>[i===void 0?l.value:`${l.value} / ${i}`]))}}}),Gc=Object.assign(Object.assign({},Be.props),{bordered:{type:Boolean,default:void 0},type:{type:String,default:"text"},placeholder:[Array,String],defaultValue:{type:[String,Array],default:null},value:[String,Array],disabled:{type:Boolean,default:void 0},size:String,rows:{type:[Number,String],default:3},round:Boolean,minlength:[String,Number],maxlength:[String,Number],clearable:Boolean,autosize:{type:[Boolean,Object],default:!1},pair:Boolean,separator:String,readonly:{type:[String,Boolean],default:!1},passivelyActivated:Boolean,showPasswordOn:String,stateful:{type:Boolean,default:!0},autofocus:Boolean,inputProps:Object,resizable:{type:Boolean,default:!0},showCount:Boolean,loading:{type:Boolean,default:void 0},allowInput:Function,renderCount:Function,onMousedown:Function,onKeydown:Function,onKeyup:[Function,Array],onInput:[Function,Array],onFocus:[Function,Array],onBlur:[Function,Array],onClick:[Function,Array],onChange:[Function,Array],onClear:[Function,Array],countGraphemes:Function,status:String,"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],textDecoration:[String,Array],attrSize:{type:Number,default:20},onInputBlur:[Function,Array],onInputFocus:[Function,Array],onDeactivate:[Function,Array],onActivate:[Function,Array],onWrapperFocus:[Function,Array],onWrapperBlur:[Function,Array],internalDeactivateOnEnter:Boolean,internalForceFocus:Boolean,internalLoadingBeforeSuffix:{type:Boolean,default:!0},showPasswordToggle:Boolean}),Xc=Se({name:"Input",props:Gc,slots:Object,setup(e){const{mergedClsPrefixRef:t,mergedBorderedRef:n,inlineThemeDisabled:o,mergedRtlRef:r,mergedComponentPropsRef:a}=ot(e),l=Be("Input","-input",Hc,Ba,e,t);bi&&To("-input-safari",jc,t);const i=T(null),s=T(null),c=T(null),f=T(null),u=T(null),p=T(null),y=T(null),h=Uc(y),b=T(null),{localeRef:w}=jo("Input"),m=T(e.defaultValue),B=_e(e,"value"),W=Et(B,m),F=Dn(e,{mergedSize:v=>{var M,oe;const{size:ze}=e;if(ze)return ze;const{mergedSize:Pe}=v||{};if(Pe!=null&&Pe.value)return Pe.value;const $e=(oe=(M=a==null?void 0:a.value)===null||M===void 0?void 0:M.Input)===null||oe===void 0?void 0:oe.size;return $e||"medium"}}),{mergedSizeRef:C,mergedDisabledRef:P,mergedStatusRef:V}=F,S=T(!1),k=T(!1),R=T(!1),K=T(!1);let j=null;const z=H(()=>{const{placeholder:v,pair:M}=e;return M?Array.isArray(v)?v:v===void 0?["",""]:[v,v]:v===void 0?[w.value.placeholder]:[v]}),G=H(()=>{const{value:v}=R,{value:M}=W,{value:oe}=z;return!v&&(Sn(M)||Array.isArray(M)&&Sn(M[0]))&&oe[0]}),E=H(()=>{const{value:v}=R,{value:M}=W,{value:oe}=z;return!v&&oe[1]&&(Sn(M)||Array.isArray(M)&&Sn(M[1]))}),J=Ue(()=>e.internalForceFocus||S.value),Q=Ue(()=>{if(P.value||e.readonly||!e.clearable||!J.value&&!k.value)return!1;const{value:v}=W,{value:M}=J;return e.pair?!!(Array.isArray(v)&&(v[0]||v[1]))&&(k.value||M):!!v&&(k.value||M)}),X=H(()=>{const{showPasswordOn:v}=e;if(v)return v;if(e.showPasswordToggle)return"click"}),te=T(!1),ue=H(()=>{const{textDecoration:v}=e;return v?Array.isArray(v)?v.map(M=>({textDecoration:M})):[{textDecoration:v}]:["",""]}),le=T(void 0),re=()=>{var v,M;if(e.type==="textarea"){const{autosize:oe}=e;if(oe&&(le.value=(M=(v=b.value)===null||v===void 0?void 0:v.$el)===null||M===void 0?void 0:M.offsetWidth),!s.value||typeof oe=="boolean")return;const{paddingTop:ze,paddingBottom:Pe,lineHeight:$e}=window.getComputedStyle(s.value),ft=Number(ze.slice(0,-2)),ht=Number(Pe.slice(0,-2)),vt=Number($e.slice(0,-2)),{value:zt}=c;if(!zt)return;if(oe.minRows){const Pt=Math.max(oe.minRows,1),on=`${ft+ht+vt*Pt}px`;zt.style.minHeight=on}if(oe.maxRows){const Pt=`${ft+ht+vt*oe.maxRows}px`;zt.style.maxHeight=Pt}}},xe=H(()=>{const{maxlength:v}=e;return v===void 0?void 0:Number(v)});nt(()=>{const{value:v}=W;Array.isArray(v)||Ye(v)});const O=Rr().proxy;function L(v,M){const{onUpdateValue:oe,"onUpdate:value":ze,onInput:Pe}=e,{nTriggerFormInput:$e}=F;oe&&ge(oe,v,M),ze&&ge(ze,v,M),Pe&&ge(Pe,v,M),m.value=v,$e()}function pe(v,M){const{onChange:oe}=e,{nTriggerFormChange:ze}=F;oe&&ge(oe,v,M),m.value=v,ze()}function fe(v){const{onBlur:M}=e,{nTriggerFormBlur:oe}=F;M&&ge(M,v),oe()}function Me(v){const{onFocus:M}=e,{nTriggerFormFocus:oe}=F;M&&ge(M,v),oe()}function Fe(v){const{onClear:M}=e;M&&ge(M,v)}function ie(v){const{onInputBlur:M}=e;M&&ge(M,v)}function Ne(v){const{onInputFocus:M}=e;M&&ge(M,v)}function Le(){const{onDeactivate:v}=e;v&&ge(v)}function Ve(){const{onActivate:v}=e;v&&ge(v)}function rt(v){const{onClick:M}=e;M&&ge(M,v)}function it(v){const{onWrapperFocus:M}=e;M&&ge(M,v)}function Ke(v){const{onWrapperBlur:M}=e;M&&ge(M,v)}function Xe(){R.value=!0}function I(v){R.value=!1,v.target===p.value?g(v,1):g(v,0)}function g(v,M=0,oe="input"){const ze=v.target.value;if(Ye(ze),v instanceof InputEvent&&!v.isComposing&&(R.value=!1),e.type==="textarea"){const{value:$e}=b;$e&&$e.syncUnifiedContainer()}if(j=ze,R.value)return;h.recordCursor();const Pe=ce(ze);if(Pe)if(!e.pair)oe==="input"?L(ze,{source:M}):pe(ze,{source:M});else{let{value:$e}=W;Array.isArray($e)?$e=[$e[0],$e[1]]:$e=["",""],$e[M]=ze,oe==="input"?L($e,{source:M}):pe($e,{source:M})}O.$forceUpdate(),Pe||mt(h.restoreCursor)}function ce(v){const{countGraphemes:M,maxlength:oe,minlength:ze}=e;if(M){let $e;if(oe!==void 0&&($e===void 0&&($e=M(v)),$e>Number(oe))||ze!==void 0&&($e===void 0&&($e=M(v)),$e<Number(oe)))return!1}const{allowInput:Pe}=e;return typeof Pe=="function"?Pe(v):!0}function ee(v){ie(v),v.relatedTarget===i.value&&Le(),v.relatedTarget!==null&&(v.relatedTarget===u.value||v.relatedTarget===p.value||v.relatedTarget===s.value)||(K.value=!1),Y(v,"blur"),y.value=null}function ne(v,M){Ne(v),S.value=!0,K.value=!0,Ve(),Y(v,"focus"),M===0?y.value=u.value:M===1?y.value=p.value:M===2&&(y.value=s.value)}function ke(v){e.passivelyActivated&&(Ke(v),Y(v,"blur"))}function A(v){e.passivelyActivated&&(S.value=!0,it(v),Y(v,"focus"))}function Y(v,M){v.relatedTarget!==null&&(v.relatedTarget===u.value||v.relatedTarget===p.value||v.relatedTarget===s.value||v.relatedTarget===i.value)||(M==="focus"?(Me(v),S.value=!0):M==="blur"&&(fe(v),S.value=!1))}function Oe(v,M){g(v,M,"change")}function he(v){rt(v)}function me(v){Fe(v),He()}function He(){e.pair?(L(["",""],{source:"clear"}),pe(["",""],{source:"clear"})):(L("",{source:"clear"}),pe("",{source:"clear"}))}function be(v){const{onMousedown:M}=e;M&&M(v);const{tagName:oe}=v.target;if(oe!=="INPUT"&&oe!=="TEXTAREA"){if(e.resizable){const{value:ze}=i;if(ze){const{left:Pe,top:$e,width:ft,height:ht}=ze.getBoundingClientRect(),vt=14;if(Pe+ft-vt<v.clientX&&v.clientX<Pe+ft&&$e+ht-vt<v.clientY&&v.clientY<$e+ht)return}}v.preventDefault(),S.value||ae()}}function lt(){var v;k.value=!0,e.type==="textarea"&&((v=b.value)===null||v===void 0||v.handleMouseEnterWrapper())}function st(){var v;k.value=!1,e.type==="textarea"&&((v=b.value)===null||v===void 0||v.handleMouseLeaveWrapper())}function tn(){P.value||X.value==="click"&&(te.value=!te.value)}function nn(v){if(P.value)return;v.preventDefault();const M=ze=>{ze.preventDefault(),Ze("mouseup",document,M)};if(tt("mouseup",document,M),X.value!=="mousedown")return;te.value=!0;const oe=()=>{te.value=!1,Ze("mouseup",document,oe)};tt("mouseup",document,oe)}function Rt(v){e.onKeyup&&ge(e.onKeyup,v)}function dt(v){switch(e.onKeydown&&ge(e.onKeydown,v),v.key){case"Escape":U();break;case"Enter":x(v);break}}function x(v){var M,oe;if(e.passivelyActivated){const{value:ze}=K;if(ze){e.internalDeactivateOnEnter&&U();return}v.preventDefault(),e.type==="textarea"?(M=s.value)===null||M===void 0||M.focus():(oe=u.value)===null||oe===void 0||oe.focus()}}function U(){e.passivelyActivated&&(K.value=!1,mt(()=>{var v;(v=i.value)===null||v===void 0||v.focus()}))}function ae(){var v,M,oe;P.value||(e.passivelyActivated?(v=i.value)===null||v===void 0||v.focus():((M=s.value)===null||M===void 0||M.focus(),(oe=u.value)===null||oe===void 0||oe.focus()))}function we(){var v;!((v=i.value)===null||v===void 0)&&v.contains(document.activeElement)&&document.activeElement.blur()}function ve(){var v,M;(v=s.value)===null||v===void 0||v.select(),(M=u.value)===null||M===void 0||M.select()}function ye(){P.value||(s.value?s.value.focus():u.value&&u.value.focus())}function Ce(){const{value:v}=i;v!=null&&v.contains(document.activeElement)&&v!==document.activeElement&&U()}function Ee(v){if(e.type==="textarea"){const{value:M}=s;M==null||M.scrollTo(v)}else{const{value:M}=u;M==null||M.scrollTo(v)}}function Ye(v){const{type:M,pair:oe,autosize:ze}=e;if(!oe&&ze)if(M==="textarea"){const{value:Pe}=c;Pe&&(Pe.textContent=`${v??""}\r
`)}else{const{value:Pe}=f;Pe&&(v?Pe.textContent=v:Pe.innerHTML="&nbsp;")}}function Wn(){re()}const bn=T({top:"0"});function Nn(v){var M;const{scrollTop:oe}=v.target;bn.value.top=`${-oe}px`,(M=b.value)===null||M===void 0||M.syncUnifiedContainer()}let At=null;Bt(()=>{const{autosize:v,type:M}=e;v&&M==="textarea"?At=Ie(W,oe=>{!Array.isArray(oe)&&oe!==j&&Ye(oe)}):At==null||At()});let Dt=null;Bt(()=>{e.type==="textarea"?Dt=Ie(W,v=>{var M;!Array.isArray(v)&&v!==j&&((M=b.value)===null||M===void 0||M.syncUnifiedContainer())}):Dt==null||Dt()}),Ge(mi,{mergedValueRef:W,maxlengthRef:xe,mergedClsPrefixRef:t,countGraphemesRef:_e(e,"countGraphemes")});const Vn={wrapperElRef:i,inputElRef:u,textareaElRef:s,isCompositing:R,clear:He,focus:ae,blur:we,select:ve,deactivate:Ce,activate:ye,scrollTo:Ee},Hn=It("Input",r,t),mn=H(()=>{const{value:v}=C,{common:{cubicBezierEaseInOut:M},self:{color:oe,borderRadius:ze,textColor:Pe,caretColor:$e,caretColorError:ft,caretColorWarning:ht,textDecorationColor:vt,border:zt,borderDisabled:Pt,borderHover:on,borderFocus:jn,placeholderColor:Kn,placeholderColorDisabled:Un,lineHeightTextarea:Gn,colorDisabled:Lt,colorFocus:Wt,textColorDisabled:wi,boxShadowFocus:xi,iconSize:Ci,colorFocusWarning:Si,boxShadowFocusWarning:ki,borderWarning:_i,borderFocusWarning:$i,borderHoverWarning:zi,colorFocusError:Pi,boxShadowFocusError:Mi,borderError:Ti,borderFocusError:Fi,borderHoverError:Oi,clearSize:Bi,clearColor:Ei,clearColorHover:Ii,clearColorPressed:Ri,iconColor:Ai,iconColorDisabled:Di,suffixTextColor:Li,countTextColor:Wi,countTextColorDisabled:Ni,iconColorHover:Vi,iconColorPressed:Hi,loadingColor:ji,loadingColorError:Ki,loadingColorWarning:Ui,fontWeight:Gi,[q("padding",v)]:Xi,[q("fontSize",v)]:Yi,[q("height",v)]:qi}}=l.value,{left:Zi,right:Ji}=Ot(Xi);return{"--n-bezier":M,"--n-count-text-color":Wi,"--n-count-text-color-disabled":Ni,"--n-color":oe,"--n-font-size":Yi,"--n-font-weight":Gi,"--n-border-radius":ze,"--n-height":qi,"--n-padding-left":Zi,"--n-padding-right":Ji,"--n-text-color":Pe,"--n-caret-color":$e,"--n-text-decoration-color":vt,"--n-border":zt,"--n-border-disabled":Pt,"--n-border-hover":on,"--n-border-focus":jn,"--n-placeholder-color":Kn,"--n-placeholder-color-disabled":Un,"--n-icon-size":Ci,"--n-line-height-textarea":Gn,"--n-color-disabled":Lt,"--n-color-focus":Wt,"--n-text-color-disabled":wi,"--n-box-shadow-focus":xi,"--n-loading-color":ji,"--n-caret-color-warning":ht,"--n-color-focus-warning":Si,"--n-box-shadow-focus-warning":ki,"--n-border-warning":_i,"--n-border-focus-warning":$i,"--n-border-hover-warning":zi,"--n-loading-color-warning":Ui,"--n-caret-color-error":ft,"--n-color-focus-error":Pi,"--n-box-shadow-focus-error":Mi,"--n-border-error":Ti,"--n-border-focus-error":Fi,"--n-border-hover-error":Oi,"--n-loading-color-error":Ki,"--n-clear-color":Ei,"--n-clear-size":Bi,"--n-clear-color-hover":Ii,"--n-clear-color-pressed":Ri,"--n-icon-color":Ai,"--n-icon-color-hover":Vi,"--n-icon-color-pressed":Hi,"--n-icon-color-disabled":Di,"--n-suffix-text-color":Li}}),wt=o?at("input",H(()=>{const{value:v}=C;return v[0]}),mn,e):void 0;return Object.assign(Object.assign({},Vn),{wrapperElRef:i,inputElRef:u,inputMirrorElRef:f,inputEl2Ref:p,textareaElRef:s,textareaMirrorElRef:c,textareaScrollbarInstRef:b,rtlEnabled:Hn,uncontrolledValue:m,mergedValue:W,passwordVisible:te,mergedPlaceholder:z,showPlaceholder1:G,showPlaceholder2:E,mergedFocus:J,isComposing:R,activated:K,showClearButton:Q,mergedSize:C,mergedDisabled:P,textDecorationStyle:ue,mergedClsPrefix:t,mergedBordered:n,mergedShowPasswordOn:X,placeholderStyle:bn,mergedStatus:V,textAreaScrollContainerWidth:le,handleTextAreaScroll:Nn,handleCompositionStart:Xe,handleCompositionEnd:I,handleInput:g,handleInputBlur:ee,handleInputFocus:ne,handleWrapperBlur:ke,handleWrapperFocus:A,handleMouseEnter:lt,handleMouseLeave:st,handleMouseDown:be,handleChange:Oe,handleClick:he,handleClear:me,handlePasswordToggleClick:tn,handlePasswordToggleMousedown:nn,handleWrapperKeydown:dt,handleWrapperKeyup:Rt,handleTextAreaMirrorResize:Wn,getTextareaScrollContainer:()=>s.value,mergedTheme:l,cssVars:o?void 0:mn,themeClass:wt==null?void 0:wt.themeClass,onRender:wt==null?void 0:wt.onRender})},render(){var e,t,n,o,r,a,l;const{mergedClsPrefix:i,mergedStatus:s,themeClass:c,type:f,countGraphemes:u,onRender:p}=this,y=this.$slots;return p==null||p(),d("div",{ref:"wrapperElRef",class:[`${i}-input`,`${i}-input--${this.mergedSize}-size`,c,s&&`${i}-input--${s}-status`,{[`${i}-input--rtl`]:this.rtlEnabled,[`${i}-input--disabled`]:this.mergedDisabled,[`${i}-input--textarea`]:f==="textarea",[`${i}-input--resizable`]:this.resizable&&!this.autosize,[`${i}-input--autosize`]:this.autosize,[`${i}-input--round`]:this.round&&f!=="textarea",[`${i}-input--pair`]:this.pair,[`${i}-input--focus`]:this.mergedFocus,[`${i}-input--stateful`]:this.stateful}],style:this.cssVars,tabindex:!this.mergedDisabled&&this.passivelyActivated&&!this.activated?0:void 0,onFocus:this.handleWrapperFocus,onBlur:this.handleWrapperBlur,onClick:this.handleClick,onMousedown:this.handleMouseDown,onMouseenter:this.handleMouseEnter,onMouseleave:this.handleMouseLeave,onCompositionstart:this.handleCompositionStart,onCompositionend:this.handleCompositionEnd,onKeyup:this.handleWrapperKeyup,onKeydown:this.handleWrapperKeydown},d("div",{class:`${i}-input-wrapper`},Re(y.prefix,h=>h&&d("div",{class:`${i}-input__prefix`},h)),f==="textarea"?d(An,{ref:"textareaScrollbarInstRef",class:`${i}-input__textarea`,container:this.getTextareaScrollContainer,theme:(t=(e=this.theme)===null||e===void 0?void 0:e.peers)===null||t===void 0?void 0:t.Scrollbar,themeOverrides:(o=(n=this.themeOverrides)===null||n===void 0?void 0:n.peers)===null||o===void 0?void 0:o.Scrollbar,triggerDisplayManually:!0,useUnifiedContainer:!0,internalHoistYRail:!0},{default:()=>{var h,b;const{textAreaScrollContainerWidth:w}=this,m={width:this.autosize&&w&&`${w}px`};return d(je,null,d("textarea",Object.assign({},this.inputProps,{ref:"textareaElRef",class:[`${i}-input__textarea-el`,(h=this.inputProps)===null||h===void 0?void 0:h.class],autofocus:this.autofocus,rows:Number(this.rows),placeholder:this.placeholder,value:this.mergedValue,disabled:this.mergedDisabled,maxlength:u?void 0:this.maxlength,minlength:u?void 0:this.minlength,readonly:this.readonly,tabindex:this.passivelyActivated&&!this.activated?-1:void 0,style:[this.textDecorationStyle[0],(b=this.inputProps)===null||b===void 0?void 0:b.style,m],onBlur:this.handleInputBlur,onFocus:B=>{this.handleInputFocus(B,2)},onInput:this.handleInput,onChange:this.handleChange,onScroll:this.handleTextAreaScroll})),this.showPlaceholder1?d("div",{class:`${i}-input__placeholder`,style:[this.placeholderStyle,m],key:"placeholder"},this.mergedPlaceholder[0]):null,this.autosize?d(ho,{onResize:this.handleTextAreaMirrorResize},{default:()=>d("div",{ref:"textareaMirrorElRef",class:`${i}-input__textarea-mirror`,key:"mirror"})}):null)}}):d("div",{class:`${i}-input__input`},d("input",Object.assign({type:f==="password"&&this.mergedShowPasswordOn&&this.passwordVisible?"text":f},this.inputProps,{ref:"inputElRef",class:[`${i}-input__input-el`,(r=this.inputProps)===null||r===void 0?void 0:r.class],style:[this.textDecorationStyle[0],(a=this.inputProps)===null||a===void 0?void 0:a.style],tabindex:this.passivelyActivated&&!this.activated?-1:(l=this.inputProps)===null||l===void 0?void 0:l.tabindex,placeholder:this.mergedPlaceholder[0],disabled:this.mergedDisabled,maxlength:u?void 0:this.maxlength,minlength:u?void 0:this.minlength,value:Array.isArray(this.mergedValue)?this.mergedValue[0]:this.mergedValue,readonly:this.readonly,autofocus:this.autofocus,size:this.attrSize,onBlur:this.handleInputBlur,onFocus:h=>{this.handleInputFocus(h,0)},onInput:h=>{this.handleInput(h,0)},onChange:h=>{this.handleChange(h,0)}})),this.showPlaceholder1?d("div",{class:`${i}-input__placeholder`},d("span",null,this.mergedPlaceholder[0])):null,this.autosize?d("div",{class:`${i}-input__input-mirror`,key:"mirror",ref:"inputMirrorElRef"}," "):null),!this.pair&&Re(y.suffix,h=>h||this.clearable||this.showCount||this.mergedShowPasswordOn||this.loading!==void 0?d("div",{class:`${i}-input__suffix`},[Re(y["clear-icon-placeholder"],b=>(this.clearable||b)&&d(Co,{clsPrefix:i,show:this.showClearButton,onClear:this.handleClear},{placeholder:()=>b,icon:()=>{var w,m;return(m=(w=this.$slots)["clear-icon"])===null||m===void 0?void 0:m.call(w)}})),this.internalLoadingBeforeSuffix?null:h,this.loading!==void 0?d(pi,{clsPrefix:i,loading:this.loading,showArrow:!1,showClear:!1,style:this.cssVars}):null,this.internalLoadingBeforeSuffix?h:null,this.showCount&&this.type!=="textarea"?d(Ir,null,{default:b=>{var w;const{renderCount:m}=this;return m?m(b):(w=y.count)===null||w===void 0?void 0:w.call(y,b)}}):null,this.mergedShowPasswordOn&&this.type==="password"?d("div",{class:`${i}-input__eye`,onMousedown:this.handlePasswordToggleMousedown,onClick:this.handlePasswordToggleClick},this.passwordVisible?Yt(y["password-visible-icon"],()=>[d(Zt,{clsPrefix:i},{default:()=>d(Hd,null)})]):Yt(y["password-invisible-icon"],()=>[d(Zt,{clsPrefix:i},{default:()=>d(jd,null)})])):null]):null)),this.pair?d("span",{class:`${i}-input__separator`},Yt(y.separator,()=>[this.separator])):null,this.pair?d("div",{class:`${i}-input-wrapper`},d("div",{class:`${i}-input__input`},d("input",{ref:"inputEl2Ref",type:this.type,class:`${i}-input__input-el`,tabindex:this.passivelyActivated&&!this.activated?-1:void 0,placeholder:this.mergedPlaceholder[1],disabled:this.mergedDisabled,maxlength:u?void 0:this.maxlength,minlength:u?void 0:this.minlength,value:Array.isArray(this.mergedValue)?this.mergedValue[1]:void 0,readonly:this.readonly,style:this.textDecorationStyle[1],onBlur:this.handleInputBlur,onFocus:h=>{this.handleInputFocus(h,1)},onInput:h=>{this.handleInput(h,1)},onChange:h=>{this.handleChange(h,1)}}),this.showPlaceholder2?d("div",{class:`${i}-input__placeholder`},d("span",null,this.mergedPlaceholder[1])):null),Re(y.suffix,h=>(this.clearable||h)&&d("div",{class:`${i}-input__suffix`},[this.clearable&&d(Co,{clsPrefix:i,show:this.showClearButton,onClear:this.handleClear},{icon:()=>{var b;return(b=y["clear-icon"])===null||b===void 0?void 0:b.call(y)},placeholder:()=>{var b;return(b=y["clear-icon-placeholder"])===null||b===void 0?void 0:b.call(y)}}),h]))):null,this.mergedBordered?d("div",{class:`${i}-input__border`}):null,this.mergedBordered?d("div",{class:`${i}-input__state-border`}):null,this.showCount&&f==="textarea"?d(Ir,null,{default:h=>{var b;const{renderCount:w}=this;return w?w(h):(b=y.count)===null||b===void 0?void 0:b.call(y,h)}}):null)}});function Bn(e){return e.type==="group"}function yi(e){return e.type==="ignored"}function fo(e,t){try{return!!(1+t.toString().toLowerCase().indexOf(e.trim().toLowerCase()))}catch{return!1}}function Yc(e,t){return{getIsGroup:Bn,getIgnored:yi,getKey(o){return Bn(o)?o.name||o.key||"key-required":o[e]},getChildren(o){return o[t]}}}function qc(e,t,n,o){if(!t)return e;function r(a){if(!Array.isArray(a))return[];const l=[];for(const i of a)if(Bn(i)){const s=r(i[o]);s.length&&l.push(Object.assign({},i,{[o]:s}))}else{if(yi(i))continue;t(n,i)&&l.push(i)}return l}return r(e)}function Zc(e,t,n){const o=new Map;return e.forEach(r=>{Bn(r)?r[n].forEach(a=>{o.set(a[t],a)}):o.set(r[t],r)}),o}function Tt(e){return Wr(e,[255,255,255,.16])}function kn(e){return Wr(e,[0,0,0,.12])}const Jc=ut("n-button-group"),Qc=D([N("button",`
 margin: 0;
 font-weight: var(--n-font-weight);
 line-height: 1;
 font-family: inherit;
 padding: var(--n-padding);
 height: var(--n-height);
 font-size: var(--n-font-size);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 width: var(--n-width);
 white-space: nowrap;
 outline: none;
 position: relative;
 z-index: auto;
 border: none;
 display: inline-flex;
 flex-wrap: nowrap;
 flex-shrink: 0;
 align-items: center;
 justify-content: center;
 user-select: none;
 -webkit-user-select: none;
 text-align: center;
 cursor: pointer;
 text-decoration: none;
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[Z("color",[_("border",{borderColor:"var(--n-border-color)"}),Z("disabled",[_("border",{borderColor:"var(--n-border-color-disabled)"})]),De("disabled",[D("&:focus",[_("state-border",{borderColor:"var(--n-border-color-focus)"})]),D("&:hover",[_("state-border",{borderColor:"var(--n-border-color-hover)"})]),D("&:active",[_("state-border",{borderColor:"var(--n-border-color-pressed)"})]),Z("pressed",[_("state-border",{borderColor:"var(--n-border-color-pressed)"})])])]),Z("disabled",{backgroundColor:"var(--n-color-disabled)",color:"var(--n-text-color-disabled)"},[_("border",{border:"var(--n-border-disabled)"})]),De("disabled",[D("&:focus",{backgroundColor:"var(--n-color-focus)",color:"var(--n-text-color-focus)"},[_("state-border",{border:"var(--n-border-focus)"})]),D("&:hover",{backgroundColor:"var(--n-color-hover)",color:"var(--n-text-color-hover)"},[_("state-border",{border:"var(--n-border-hover)"})]),D("&:active",{backgroundColor:"var(--n-color-pressed)",color:"var(--n-text-color-pressed)"},[_("state-border",{border:"var(--n-border-pressed)"})]),Z("pressed",{backgroundColor:"var(--n-color-pressed)",color:"var(--n-text-color-pressed)"},[_("state-border",{border:"var(--n-border-pressed)"})])]),Z("loading","cursor: wait;"),N("base-wave",`
 pointer-events: none;
 top: 0;
 right: 0;
 bottom: 0;
 left: 0;
 animation-iteration-count: 1;
 animation-duration: var(--n-ripple-duration);
 animation-timing-function: var(--n-bezier-ease-out), var(--n-bezier-ease-out);
 `,[Z("active",{zIndex:1,animationName:"button-wave-spread, button-wave-opacity"})]),gn&&"MozBoxSizing"in document.createElement("div").style?D("&::moz-focus-inner",{border:0}):null,_("border, state-border",`
 position: absolute;
 left: 0;
 top: 0;
 right: 0;
 bottom: 0;
 border-radius: inherit;
 transition: border-color .3s var(--n-bezier);
 pointer-events: none;
 `),_("border",`
 border: var(--n-border);
 `),_("state-border",`
 border: var(--n-border);
 border-color: #0000;
 z-index: 1;
 `),_("icon",`
 margin: var(--n-icon-margin);
 margin-left: 0;
 height: var(--n-icon-size);
 width: var(--n-icon-size);
 max-width: var(--n-icon-size);
 font-size: var(--n-icon-size);
 position: relative;
 flex-shrink: 0;
 `,[N("icon-slot",`
 height: var(--n-icon-size);
 width: var(--n-icon-size);
 position: absolute;
 left: 0;
 top: 50%;
 transform: translateY(-50%);
 display: flex;
 align-items: center;
 justify-content: center;
 `,[zn({top:"50%",originalTransform:"translateY(-50%)"})]),Lc()]),_("content",`
 display: flex;
 align-items: center;
 flex-wrap: nowrap;
 min-width: 0;
 `,[D("~",[_("icon",{margin:"var(--n-icon-margin)",marginRight:0})])]),Z("block",`
 display: flex;
 width: 100%;
 `),Z("dashed",[_("border, state-border",{borderStyle:"dashed !important"})]),Z("disabled",{cursor:"not-allowed",opacity:"var(--n-opacity-disabled)"})]),D("@keyframes button-wave-spread",{from:{boxShadow:"0 0 0.5px 0 var(--n-ripple-color)"},to:{boxShadow:"0 0 0.5px 4.5px var(--n-ripple-color)"}}),D("@keyframes button-wave-opacity",{from:{opacity:"var(--n-wave-opacity)"},to:{opacity:0}})]),eu=Object.assign(Object.assign({},Be.props),{color:String,textColor:String,text:Boolean,block:Boolean,loading:Boolean,disabled:Boolean,circle:Boolean,size:String,ghost:Boolean,round:Boolean,secondary:Boolean,tertiary:Boolean,quaternary:Boolean,strong:Boolean,focusable:{type:Boolean,default:!0},keyboard:{type:Boolean,default:!0},tag:{type:String,default:"button"},type:{type:String,default:"default"},dashed:Boolean,renderIcon:Function,iconPlacement:{type:String,default:"left"},attrType:{type:String,default:"button"},bordered:{type:Boolean,default:!0},onClick:[Function,Array],nativeFocusBehavior:{type:Boolean,default:!bi},spinProps:Object}),tu=Se({name:"Button",props:eu,slots:Object,setup(e){const t=T(null),n=T(null),o=T(!1),r=Ue(()=>!e.quaternary&&!e.tertiary&&!e.secondary&&!e.text&&(!e.color||e.ghost||e.dashed)&&e.bordered),a=We(Jc,{}),{inlineThemeDisabled:l,mergedClsPrefixRef:i,mergedRtlRef:s,mergedComponentPropsRef:c}=ot(e),{mergedSizeRef:f}=Dn({},{defaultSize:"medium",mergedSize:C=>{var P,V;const{size:S}=e;if(S)return S;const{size:k}=a;if(k)return k;const{mergedSize:R}=C||{};if(R)return R.value;const K=(V=(P=c==null?void 0:c.value)===null||P===void 0?void 0:P.Button)===null||V===void 0?void 0:V.size;return K||"medium"}}),u=H(()=>e.focusable&&!e.disabled),p=C=>{var P;u.value||C.preventDefault(),!e.nativeFocusBehavior&&(C.preventDefault(),!e.disabled&&u.value&&((P=t.value)===null||P===void 0||P.focus({preventScroll:!0})))},y=C=>{var P;if(!e.disabled&&!e.loading){const{onClick:V}=e;V&&ge(V,C),e.text||(P=n.value)===null||P===void 0||P.play()}},h=C=>{switch(C.key){case"Enter":if(!e.keyboard)return;o.value=!1}},b=C=>{switch(C.key){case"Enter":if(!e.keyboard||e.loading){C.preventDefault();return}o.value=!0}},w=()=>{o.value=!1},m=Be("Button","-button",Qc,Ia,e,i),B=It("Button",s,i),W=H(()=>{const C=m.value,{common:{cubicBezierEaseInOut:P,cubicBezierEaseOut:V},self:S}=C,{rippleDuration:k,opacityDisabled:R,fontWeight:K,fontWeightStrong:j}=S,z=f.value,{dashed:G,type:E,ghost:J,text:Q,color:X,round:te,circle:ue,textColor:le,secondary:re,tertiary:xe,quaternary:O,strong:L}=e,pe={"--n-font-weight":L?j:K};let fe={"--n-color":"initial","--n-color-hover":"initial","--n-color-pressed":"initial","--n-color-focus":"initial","--n-color-disabled":"initial","--n-ripple-color":"initial","--n-text-color":"initial","--n-text-color-hover":"initial","--n-text-color-pressed":"initial","--n-text-color-focus":"initial","--n-text-color-disabled":"initial"};const Me=E==="tertiary",Fe=E==="default",ie=Me?"default":E;if(Q){const ee=le||X;fe={"--n-color":"#0000","--n-color-hover":"#0000","--n-color-pressed":"#0000","--n-color-focus":"#0000","--n-color-disabled":"#0000","--n-ripple-color":"#0000","--n-text-color":ee||S[q("textColorText",ie)],"--n-text-color-hover":ee?Tt(ee):S[q("textColorTextHover",ie)],"--n-text-color-pressed":ee?kn(ee):S[q("textColorTextPressed",ie)],"--n-text-color-focus":ee?Tt(ee):S[q("textColorTextHover",ie)],"--n-text-color-disabled":ee||S[q("textColorTextDisabled",ie)]}}else if(J||G){const ee=le||X;fe={"--n-color":"#0000","--n-color-hover":"#0000","--n-color-pressed":"#0000","--n-color-focus":"#0000","--n-color-disabled":"#0000","--n-ripple-color":X||S[q("rippleColor",ie)],"--n-text-color":ee||S[q("textColorGhost",ie)],"--n-text-color-hover":ee?Tt(ee):S[q("textColorGhostHover",ie)],"--n-text-color-pressed":ee?kn(ee):S[q("textColorGhostPressed",ie)],"--n-text-color-focus":ee?Tt(ee):S[q("textColorGhostHover",ie)],"--n-text-color-disabled":ee||S[q("textColorGhostDisabled",ie)]}}else if(re){const ee=Fe?S.textColor:Me?S.textColorTertiary:S[q("color",ie)],ne=X||ee,ke=E!=="default"&&E!=="tertiary";fe={"--n-color":ke?yn(ne,{alpha:Number(S.colorOpacitySecondary)}):S.colorSecondary,"--n-color-hover":ke?yn(ne,{alpha:Number(S.colorOpacitySecondaryHover)}):S.colorSecondaryHover,"--n-color-pressed":ke?yn(ne,{alpha:Number(S.colorOpacitySecondaryPressed)}):S.colorSecondaryPressed,"--n-color-focus":ke?yn(ne,{alpha:Number(S.colorOpacitySecondaryHover)}):S.colorSecondaryHover,"--n-color-disabled":S.colorSecondary,"--n-ripple-color":"#0000","--n-text-color":ne,"--n-text-color-hover":ne,"--n-text-color-pressed":ne,"--n-text-color-focus":ne,"--n-text-color-disabled":ne}}else if(xe||O){const ee=Fe?S.textColor:Me?S.textColorTertiary:S[q("color",ie)],ne=X||ee;xe?(fe["--n-color"]=S.colorTertiary,fe["--n-color-hover"]=S.colorTertiaryHover,fe["--n-color-pressed"]=S.colorTertiaryPressed,fe["--n-color-focus"]=S.colorSecondaryHover,fe["--n-color-disabled"]=S.colorTertiary):(fe["--n-color"]=S.colorQuaternary,fe["--n-color-hover"]=S.colorQuaternaryHover,fe["--n-color-pressed"]=S.colorQuaternaryPressed,fe["--n-color-focus"]=S.colorQuaternaryHover,fe["--n-color-disabled"]=S.colorQuaternary),fe["--n-ripple-color"]="#0000",fe["--n-text-color"]=ne,fe["--n-text-color-hover"]=ne,fe["--n-text-color-pressed"]=ne,fe["--n-text-color-focus"]=ne,fe["--n-text-color-disabled"]=ne}else fe={"--n-color":X||S[q("color",ie)],"--n-color-hover":X?Tt(X):S[q("colorHover",ie)],"--n-color-pressed":X?kn(X):S[q("colorPressed",ie)],"--n-color-focus":X?Tt(X):S[q("colorFocus",ie)],"--n-color-disabled":X||S[q("colorDisabled",ie)],"--n-ripple-color":X||S[q("rippleColor",ie)],"--n-text-color":le||(X?S.textColorPrimary:Me?S.textColorTertiary:S[q("textColor",ie)]),"--n-text-color-hover":le||(X?S.textColorHoverPrimary:S[q("textColorHover",ie)]),"--n-text-color-pressed":le||(X?S.textColorPressedPrimary:S[q("textColorPressed",ie)]),"--n-text-color-focus":le||(X?S.textColorFocusPrimary:S[q("textColorFocus",ie)]),"--n-text-color-disabled":le||(X?S.textColorDisabledPrimary:S[q("textColorDisabled",ie)])};let Ne={"--n-border":"initial","--n-border-hover":"initial","--n-border-pressed":"initial","--n-border-focus":"initial","--n-border-disabled":"initial"};Q?Ne={"--n-border":"none","--n-border-hover":"none","--n-border-pressed":"none","--n-border-focus":"none","--n-border-disabled":"none"}:Ne={"--n-border":S[q("border",ie)],"--n-border-hover":S[q("borderHover",ie)],"--n-border-pressed":S[q("borderPressed",ie)],"--n-border-focus":S[q("borderFocus",ie)],"--n-border-disabled":S[q("borderDisabled",ie)]};const{[q("height",z)]:Le,[q("fontSize",z)]:Ve,[q("padding",z)]:rt,[q("paddingRound",z)]:it,[q("iconSize",z)]:Ke,[q("borderRadius",z)]:Xe,[q("iconMargin",z)]:I,waveOpacity:g}=S,ce={"--n-width":ue&&!Q?Le:"initial","--n-height":Q?"initial":Le,"--n-font-size":Ve,"--n-padding":ue||Q?"initial":te?it:rt,"--n-icon-size":Ke,"--n-icon-margin":I,"--n-border-radius":Q?"initial":ue||te?Le:Xe};return Object.assign(Object.assign(Object.assign(Object.assign({"--n-bezier":P,"--n-bezier-ease-out":V,"--n-ripple-duration":k,"--n-opacity-disabled":R,"--n-wave-opacity":g},pe),fe),Ne),ce)}),F=l?at("button",H(()=>{let C="";const{dashed:P,type:V,ghost:S,text:k,color:R,round:K,circle:j,textColor:z,secondary:G,tertiary:E,quaternary:J,strong:Q}=e;P&&(C+="a"),S&&(C+="b"),k&&(C+="c"),K&&(C+="d"),j&&(C+="e"),G&&(C+="f"),E&&(C+="g"),J&&(C+="h"),Q&&(C+="i"),R&&(C+=`j${Tn(R)}`),z&&(C+=`k${Tn(z)}`);const{value:X}=f;return C+=`l${X[0]}`,C+=`m${V[0]}`,C}),W,e):void 0;return{selfElRef:t,waveElRef:n,mergedClsPrefix:i,mergedFocusable:u,mergedSize:f,showBorder:r,enterPressed:o,rtlEnabled:B,handleMousedown:p,handleKeydown:b,handleBlur:w,handleKeyup:h,handleClick:y,customColorCssVars:H(()=>{const{color:C}=e;if(!C)return null;const P=Tt(C);return{"--n-border-color":C,"--n-border-color-hover":P,"--n-border-color-pressed":kn(C),"--n-border-color-focus":P,"--n-border-color-disabled":C}}),cssVars:l?void 0:W,themeClass:F==null?void 0:F.themeClass,onRender:F==null?void 0:F.onRender}},render(){const{mergedClsPrefix:e,tag:t,onRender:n}=this;n==null||n();const o=Re(this.$slots.default,r=>r&&d("span",{class:`${e}-button__content`},r));return d(t,{ref:"selfElRef",class:[this.themeClass,`${e}-button`,`${e}-button--${this.type}-type`,`${e}-button--${this.mergedSize}-type`,this.rtlEnabled&&`${e}-button--rtl`,this.disabled&&`${e}-button--disabled`,this.block&&`${e}-button--block`,this.enterPressed&&`${e}-button--pressed`,!this.text&&this.dashed&&`${e}-button--dashed`,this.color&&`${e}-button--color`,this.secondary&&`${e}-button--secondary`,this.loading&&`${e}-button--loading`,this.ghost&&`${e}-button--ghost`],tabindex:this.mergedFocusable?0:-1,type:this.attrType,style:this.cssVars,disabled:this.disabled,onClick:this.handleClick,onBlur:this.handleBlur,onMousedown:this.handleMousedown,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},this.iconPlacement==="right"&&o,d(Ea,{width:!0},{default:()=>Re(this.$slots.icon,r=>(this.loading||this.renderIcon||r)&&d("span",{class:`${e}-button__icon`,style:{margin:qt(this.$slots.default)?"0":""}},d(Mo,null,{default:()=>this.loading?d(vn,Object.assign({clsPrefix:e,key:"loading",class:`${e}-icon-slot`,strokeWidth:20},this.spinProps)):d("div",{key:"icon",class:`${e}-icon-slot`,role:"none"},this.renderIcon?this.renderIcon():r)})))}),this.iconPlacement==="left"&&o,this.text?null:d(Nc,{ref:"waveElRef",clsPrefix:e}),this.showBorder?d("div",{"aria-hidden":!0,class:`${e}-button__border`,style:this.customColorCssVars}):null,this.showBorder?d("div",{"aria-hidden":!0,class:`${e}-button__state-border`,style:this.customColorCssVars}):null)}}),nu=D([N("select",`
 z-index: auto;
 outline: none;
 width: 100%;
 position: relative;
 font-weight: var(--n-font-weight);
 `),N("select-menu",`
 margin: 4px 0;
 box-shadow: var(--n-menu-box-shadow);
 `,[vi({originalTransition:"background-color .3s var(--n-bezier), box-shadow .3s var(--n-bezier)"})])]),ou=Object.assign(Object.assign({},Be.props),{to:yt.propTo,bordered:{type:Boolean,default:void 0},clearable:Boolean,clearCreatedOptionsOnClear:{type:Boolean,default:!0},clearFilterAfterSelect:{type:Boolean,default:!0},options:{type:Array,default:()=>[]},defaultValue:{type:[String,Number,Array],default:null},keyboard:{type:Boolean,default:!0},value:[String,Number,Array],placeholder:String,menuProps:Object,multiple:Boolean,size:String,menuSize:{type:String},filterable:Boolean,disabled:{type:Boolean,default:void 0},remote:Boolean,loading:Boolean,filter:Function,placement:{type:String,default:"bottom-start"},widthMode:{type:String,default:"trigger"},tag:Boolean,onCreate:Function,fallbackOption:{type:[Function,Boolean],default:void 0},show:{type:Boolean,default:void 0},showArrow:{type:Boolean,default:!0},maxTagCount:[Number,String],ellipsisTagPopoverProps:Object,consistentMenuWidth:{type:Boolean,default:!0},virtualScroll:{type:Boolean,default:!0},labelField:{type:String,default:"label"},valueField:{type:String,default:"value"},childrenField:{type:String,default:"children"},renderLabel:Function,renderOption:Function,renderTag:Function,"onUpdate:value":[Function,Array],inputProps:Object,nodeProps:Function,ignoreComposition:{type:Boolean,default:!0},showOnFocus:Boolean,onUpdateValue:[Function,Array],onBlur:[Function,Array],onClear:[Function,Array],onFocus:[Function,Array],onScroll:[Function,Array],onSearch:[Function,Array],onUpdateShow:[Function,Array],"onUpdate:show":[Function,Array],displayDirective:{type:String,default:"show"},resetMenuOnOptionsChange:{type:Boolean,default:!0},status:String,showCheckmark:{type:Boolean,default:!0},scrollbarProps:Object,onChange:[Function,Array],items:Array}),ru=Se({name:"Select",props:ou,slots:Object,setup(e){const{mergedClsPrefixRef:t,mergedBorderedRef:n,namespaceRef:o,inlineThemeDisabled:r,mergedComponentPropsRef:a}=ot(e),l=Be("Select","-select",nu,Ra,e,t),i=T(e.defaultValue),s=_e(e,"value"),c=Et(s,i),f=T(!1),u=T(""),p=Fo(e,["items","options"]),y=T([]),h=T([]),b=H(()=>h.value.concat(y.value).concat(p.value)),w=H(()=>{const{filter:x}=e;if(x)return x;const{labelField:U,valueField:ae}=e;return(we,ve)=>{if(!ve)return!1;const ye=ve[U];if(typeof ye=="string")return fo(we,ye);const Ce=ve[ae];return typeof Ce=="string"?fo(we,Ce):typeof Ce=="number"?fo(we,String(Ce)):!1}}),m=H(()=>{if(e.remote)return p.value;{const{value:x}=b,{value:U}=u;return!U.length||!e.filterable?x:qc(x,w.value,U,e.childrenField)}}),B=H(()=>{const{valueField:x,childrenField:U}=e,ae=Yc(x,U);return bc(m.value,ae)}),W=H(()=>Zc(b.value,e.valueField,e.childrenField)),F=T(!1),C=Et(_e(e,"show"),F),P=T(null),V=T(null),S=T(null),{localeRef:k}=jo("Select"),R=H(()=>{var x;return(x=e.placeholder)!==null&&x!==void 0?x:k.value.placeholder}),K=[],j=T(new Map),z=H(()=>{const{fallbackOption:x}=e;if(x===void 0){const{labelField:U,valueField:ae}=e;return we=>({[U]:String(we),[ae]:we})}return x===!1?!1:U=>Object.assign(x(U),{value:U})});function G(x){const U=e.remote,{value:ae}=j,{value:we}=W,{value:ve}=z,ye=[];return x.forEach(Ce=>{if(we.has(Ce))ye.push(we.get(Ce));else if(U&&ae.has(Ce))ye.push(ae.get(Ce));else if(ve){const Ee=ve(Ce);Ee&&ye.push(Ee)}}),ye}const E=H(()=>{if(e.multiple){const{value:x}=c;return Array.isArray(x)?G(x):[]}return null}),J=H(()=>{const{value:x}=c;return!e.multiple&&!Array.isArray(x)?x===null?null:G([x])[0]||null:null}),Q=Dn(e,{mergedSize:x=>{var U,ae;const{size:we}=e;if(we)return we;const{mergedSize:ve}=x||{};if(ve!=null&&ve.value)return ve.value;const ye=(ae=(U=a==null?void 0:a.value)===null||U===void 0?void 0:U.Select)===null||ae===void 0?void 0:ae.size;return ye||"medium"}}),{mergedSizeRef:X,mergedDisabledRef:te,mergedStatusRef:ue}=Q;function le(x,U){const{onChange:ae,"onUpdate:value":we,onUpdateValue:ve}=e,{nTriggerFormChange:ye,nTriggerFormInput:Ce}=Q;ae&&ge(ae,x,U),ve&&ge(ve,x,U),we&&ge(we,x,U),i.value=x,ye(),Ce()}function re(x){const{onBlur:U}=e,{nTriggerFormBlur:ae}=Q;U&&ge(U,x),ae()}function xe(){const{onClear:x}=e;x&&ge(x)}function O(x){const{onFocus:U,showOnFocus:ae}=e,{nTriggerFormFocus:we}=Q;U&&ge(U,x),we(),ae&&Fe()}function L(x){const{onSearch:U}=e;U&&ge(U,x)}function pe(x){const{onScroll:U}=e;U&&ge(U,x)}function fe(){var x;const{remote:U,multiple:ae}=e;if(U){const{value:we}=j;if(ae){const{valueField:ve}=e;(x=E.value)===null||x===void 0||x.forEach(ye=>{we.set(ye[ve],ye)})}else{const ve=J.value;ve&&we.set(ve[e.valueField],ve)}}}function Me(x){const{onUpdateShow:U,"onUpdate:show":ae}=e;U&&ge(U,x),ae&&ge(ae,x),F.value=x}function Fe(){te.value||(Me(!0),F.value=!0,e.filterable&&st())}function ie(){Me(!1)}function Ne(){u.value="",h.value=K}const Le=T(!1);function Ve(){e.filterable&&(Le.value=!0)}function rt(){e.filterable&&(Le.value=!1,C.value||Ne())}function it(){te.value||(C.value?e.filterable?st():ie():Fe())}function Ke(x){var U,ae;!((ae=(U=S.value)===null||U===void 0?void 0:U.selfRef)===null||ae===void 0)&&ae.contains(x.relatedTarget)||(f.value=!1,re(x),ie())}function Xe(x){O(x),f.value=!0}function I(){f.value=!0}function g(x){var U;!((U=P.value)===null||U===void 0)&&U.$el.contains(x.relatedTarget)||(f.value=!1,re(x),ie())}function ce(){var x;(x=P.value)===null||x===void 0||x.focus(),ie()}function ee(x){var U;C.value&&(!((U=P.value)===null||U===void 0)&&U.$el.contains($n(x))||ie())}function ne(x){if(!Array.isArray(x))return[];if(z.value)return Array.from(x);{const{remote:U}=e,{value:ae}=W;if(U){const{value:we}=j;return x.filter(ve=>ae.has(ve)||we.has(ve))}else return x.filter(we=>ae.has(we))}}function ke(x){A(x.rawNode)}function A(x){if(te.value)return;const{tag:U,remote:ae,clearFilterAfterSelect:we,valueField:ve}=e;if(U&&!ae){const{value:ye}=h,Ce=ye[0]||null;if(Ce){const Ee=y.value;Ee.length?Ee.push(Ce):y.value=[Ce],h.value=K}}if(ae&&j.value.set(x[ve],x),e.multiple){const ye=ne(c.value),Ce=ye.findIndex(Ee=>Ee===x[ve]);if(~Ce){if(ye.splice(Ce,1),U&&!ae){const Ee=Y(x[ve]);~Ee&&(y.value.splice(Ee,1),we&&(u.value=""))}}else ye.push(x[ve]),we&&(u.value="");le(ye,G(ye))}else{if(U&&!ae){const ye=Y(x[ve]);~ye?y.value=[y.value[ye]]:y.value=K}lt(),ie(),le(x[ve],x)}}function Y(x){return y.value.findIndex(ae=>ae[e.valueField]===x)}function Oe(x){C.value||Fe();const{value:U}=x.target;u.value=U;const{tag:ae,remote:we}=e;if(L(U),ae&&!we){if(!U){h.value=K;return}const{onCreate:ve}=e,ye=ve?ve(U):{[e.labelField]:U,[e.valueField]:U},{valueField:Ce,labelField:Ee}=e;p.value.some(Ye=>Ye[Ce]===ye[Ce]||Ye[Ee]===ye[Ee])||y.value.some(Ye=>Ye[Ce]===ye[Ce]||Ye[Ee]===ye[Ee])?h.value=K:h.value=[ye]}}function he(x){x.stopPropagation();const{multiple:U,tag:ae,remote:we,clearCreatedOptionsOnClear:ve}=e;!U&&e.filterable&&ie(),ae&&!we&&ve&&(y.value=K),xe(),U?le([],[]):le(null,null)}function me(x){!cn(x,"action")&&!cn(x,"empty")&&!cn(x,"header")&&x.preventDefault()}function He(x){pe(x)}function be(x){var U,ae,we,ve,ye;if(!e.keyboard){x.preventDefault();return}switch(x.key){case" ":if(e.filterable)break;x.preventDefault();case"Enter":if(!(!((U=P.value)===null||U===void 0)&&U.isComposing)){if(C.value){const Ce=(ae=S.value)===null||ae===void 0?void 0:ae.getPendingTmNode();Ce?ke(Ce):e.filterable||(ie(),lt())}else if(Fe(),e.tag&&Le.value){const Ce=h.value[0];if(Ce){const Ee=Ce[e.valueField],{value:Ye}=c;e.multiple&&Array.isArray(Ye)&&Ye.includes(Ee)||A(Ce)}}}x.preventDefault();break;case"ArrowUp":if(x.preventDefault(),e.loading)return;C.value&&((we=S.value)===null||we===void 0||we.prev());break;case"ArrowDown":if(x.preventDefault(),e.loading)return;C.value?(ve=S.value)===null||ve===void 0||ve.next():Fe();break;case"Escape":C.value&&(Ol(x),ie()),(ye=P.value)===null||ye===void 0||ye.focus();break}}function lt(){var x;(x=P.value)===null||x===void 0||x.focus()}function st(){var x;(x=P.value)===null||x===void 0||x.focusInput()}function tn(){var x;C.value&&((x=V.value)===null||x===void 0||x.syncPosition())}fe(),Ie(_e(e,"options"),fe);const nn={focus:()=>{var x;(x=P.value)===null||x===void 0||x.focus()},focusInput:()=>{var x;(x=P.value)===null||x===void 0||x.focusInput()},blur:()=>{var x;(x=P.value)===null||x===void 0||x.blur()},blurInput:()=>{var x;(x=P.value)===null||x===void 0||x.blurInput()}},Rt=H(()=>{const{self:{menuBoxShadow:x}}=l.value;return{"--n-menu-box-shadow":x}}),dt=r?at("select",void 0,Rt,e):void 0;return Object.assign(Object.assign({},nn),{mergedStatus:ue,mergedClsPrefix:t,mergedBordered:n,namespace:o,treeMate:B,isMounted:En(),triggerRef:P,menuRef:S,pattern:u,uncontrolledShow:F,mergedShow:C,adjustedTo:yt(e),uncontrolledValue:i,mergedValue:c,followerRef:V,localizedPlaceholder:R,selectedOption:J,selectedOptions:E,mergedSize:X,mergedDisabled:te,focused:f,activeWithoutMenuOpen:Le,inlineThemeDisabled:r,onTriggerInputFocus:Ve,onTriggerInputBlur:rt,handleTriggerOrMenuResize:tn,handleMenuFocus:I,handleMenuBlur:g,handleMenuTabOut:ce,handleTriggerClick:it,handleToggle:ke,handleDeleteOption:A,handlePatternInput:Oe,handleClear:he,handleTriggerBlur:Ke,handleTriggerFocus:Xe,handleKeydown:be,handleMenuAfterLeave:Ne,handleMenuClickOutside:ee,handleMenuScroll:He,handleMenuKeydown:be,handleMenuMousedown:me,mergedTheme:l,cssVars:r?void 0:Rt,themeClass:dt==null?void 0:dt.themeClass,onRender:dt==null?void 0:dt.onRender})},render(){return d("div",{class:`${this.mergedClsPrefix}-select`},d(Xr,null,{default:()=>[d(Yr,null,{default:()=>d(Dc,{ref:"triggerRef",inlineThemeDisabled:this.inlineThemeDisabled,status:this.mergedStatus,inputProps:this.inputProps,clsPrefix:this.mergedClsPrefix,showArrow:this.showArrow,maxTagCount:this.maxTagCount,ellipsisTagPopoverProps:this.ellipsisTagPopoverProps,bordered:this.mergedBordered,active:this.activeWithoutMenuOpen||this.mergedShow,pattern:this.pattern,placeholder:this.localizedPlaceholder,selectedOption:this.selectedOption,selectedOptions:this.selectedOptions,multiple:this.multiple,renderTag:this.renderTag,renderLabel:this.renderLabel,filterable:this.filterable,clearable:this.clearable,disabled:this.mergedDisabled,size:this.mergedSize,theme:this.mergedTheme.peers.InternalSelection,labelField:this.labelField,valueField:this.valueField,themeOverrides:this.mergedTheme.peerOverrides.InternalSelection,loading:this.loading,focused:this.focused,onClick:this.handleTriggerClick,onDeleteOption:this.handleDeleteOption,onPatternInput:this.handlePatternInput,onClear:this.handleClear,onBlur:this.handleTriggerBlur,onFocus:this.handleTriggerFocus,onKeydown:this.handleKeydown,onPatternBlur:this.onTriggerInputBlur,onPatternFocus:this.onTriggerInputFocus,onResize:this.handleTriggerOrMenuResize,ignoreComposition:this.ignoreComposition},{arrow:()=>{var e,t;return[(t=(e=this.$slots).arrow)===null||t===void 0?void 0:t.call(e)]}})}),d(Jr,{ref:"followerRef",show:this.mergedShow,to:this.adjustedTo,teleportDisabled:this.adjustedTo===yt.tdkey,containerClass:this.namespace,width:this.consistentMenuWidth?"target":void 0,minWidth:"target",placement:this.placement},{default:()=>d(Qt,{name:"fade-in-scale-up-transition",appear:this.isMounted,onAfterLeave:this.handleMenuAfterLeave},{default:()=>{var e,t,n;return this.mergedShow||this.displayDirective==="show"?((e=this.onRender)===null||e===void 0||e.call(this),_t(d(Sc,Object.assign({},this.menuProps,{ref:"menuRef",onResize:this.handleTriggerOrMenuResize,inlineThemeDisabled:this.inlineThemeDisabled,virtualScroll:this.consistentMenuWidth&&this.virtualScroll,class:[`${this.mergedClsPrefix}-select-menu`,this.themeClass,(t=this.menuProps)===null||t===void 0?void 0:t.class],clsPrefix:this.mergedClsPrefix,focusable:!0,labelField:this.labelField,valueField:this.valueField,autoPending:!0,nodeProps:this.nodeProps,theme:this.mergedTheme.peers.InternalSelectMenu,themeOverrides:this.mergedTheme.peerOverrides.InternalSelectMenu,treeMate:this.treeMate,multiple:this.multiple,size:this.menuSize,renderOption:this.renderOption,renderLabel:this.renderLabel,value:this.mergedValue,style:[(n=this.menuProps)===null||n===void 0?void 0:n.style,this.cssVars],onToggle:this.handleToggle,onScroll:this.handleMenuScroll,onFocus:this.handleMenuFocus,onBlur:this.handleMenuBlur,onKeydown:this.handleMenuKeydown,onTabOut:this.handleMenuTabOut,onMousedown:this.handleMenuMousedown,show:this.mergedShow,showCheckmark:this.showCheckmark,resetMenuOnOptionsChange:this.resetMenuOnOptionsChange,scrollbarProps:this.scrollbarProps}),{empty:()=>{var o,r;return[(r=(o=this.$slots).empty)===null||r===void 0?void 0:r.call(o)]},header:()=>{var o,r;return[(r=(o=this.$slots).header)===null||r===void 0?void 0:r.call(o)]},action:()=>{var o,r;return[(r=(o=this.$slots).action)===null||r===void 0?void 0:r.call(o)]}}),this.displayDirective==="show"?[[Pn,this.mergedShow],[hn,this.handleMenuClickOutside,void 0,{capture:!0}]]:[[hn,this.handleMenuClickOutside,void 0,{capture:!0}]])):null}})})]}))}}),iu=Se({name:"NDrawerContent",inheritAttrs:!1,props:{blockScroll:Boolean,show:{type:Boolean,default:void 0},displayDirective:{type:String,required:!0},placement:{type:String,required:!0},contentClass:String,contentStyle:[Object,String],nativeScrollbar:{type:Boolean,required:!0},scrollbarProps:Object,trapFocus:{type:Boolean,default:!0},autoFocus:{type:Boolean,default:!0},showMask:{type:[Boolean,String],required:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,onClickoutside:Function,onAfterLeave:Function,onAfterEnter:Function,onEsc:Function},setup(e){const t=T(!!e.show),n=T(null),o=We(Eo);let r=0,a="",l=null;const i=T(!1),s=T(!1),c=H(()=>e.placement==="top"||e.placement==="bottom"),{mergedClsPrefixRef:f,mergedRtlRef:u}=ot(e),p=It("Drawer",u,f),y=P,h=k=>{s.value=!0,r=c.value?k.clientY:k.clientX,a=document.body.style.cursor,document.body.style.cursor=c.value?"ns-resize":"ew-resize",document.body.addEventListener("mousemove",C),document.body.addEventListener("mouseleave",y),document.body.addEventListener("mouseup",P)},b=()=>{l!==null&&(window.clearTimeout(l),l=null),s.value?i.value=!0:l=window.setTimeout(()=>{i.value=!0},300)},w=()=>{l!==null&&(window.clearTimeout(l),l=null),i.value=!1},{doUpdateHeight:m,doUpdateWidth:B}=o,W=k=>{const{maxWidth:R}=e;if(R&&k>R)return R;const{minWidth:K}=e;return K&&k<K?K:k},F=k=>{const{maxHeight:R}=e;if(R&&k>R)return R;const{minHeight:K}=e;return K&&k<K?K:k};function C(k){var R,K;if(s.value)if(c.value){let j=((R=n.value)===null||R===void 0?void 0:R.offsetHeight)||0;const z=r-k.clientY;j+=e.placement==="bottom"?z:-z,j=F(j),m(j),r=k.clientY}else{let j=((K=n.value)===null||K===void 0?void 0:K.offsetWidth)||0;const z=r-k.clientX;j+=e.placement==="right"?z:-z,j=W(j),B(j),r=k.clientX}}function P(){s.value&&(r=0,s.value=!1,document.body.style.cursor=a,document.body.removeEventListener("mousemove",C),document.body.removeEventListener("mouseup",P),document.body.removeEventListener("mouseleave",y))}Bt(()=>{e.show&&(t.value=!0)}),Ie(()=>e.show,k=>{k||P()}),Je(()=>{P()});const V=H(()=>{const{show:k}=e,R=[[Pn,k]];return e.showMask||R.push([hn,e.onClickoutside,void 0,{capture:!0}]),R});function S(){var k;t.value=!1,(k=e.onAfterLeave)===null||k===void 0||k.call(e)}return ul(H(()=>e.blockScroll&&t.value)),Ge(Bo,n),Ge(Ro,null),Ge(Io,null),{bodyRef:n,rtlEnabled:p,mergedClsPrefix:o.mergedClsPrefixRef,isMounted:o.isMountedRef,mergedTheme:o.mergedThemeRef,displayed:t,transitionName:H(()=>({right:"slide-in-from-right-transition",left:"slide-in-from-left-transition",top:"slide-in-from-top-transition",bottom:"slide-in-from-bottom-transition"})[e.placement]),handleAfterLeave:S,bodyDirectives:V,handleMousedownResizeTrigger:h,handleMouseenterResizeTrigger:b,handleMouseleaveResizeTrigger:w,isDragging:s,isHoverOnResizeTrigger:i}},render(){const{$slots:e,mergedClsPrefix:t}=this;return this.displayDirective==="show"||this.displayed||this.show?_t(d("div",{role:"none"},d(ri,{disabled:!this.showMask||!this.trapFocus,active:this.show,autoFocus:this.autoFocus,onEsc:this.onEsc},{default:()=>d(Qt,{name:this.transitionName,appear:this.isMounted,onAfterEnter:this.onAfterEnter,onAfterLeave:this.handleAfterLeave},{default:()=>_t(d("div",$o(this.$attrs,{role:"dialog",ref:"bodyRef","aria-modal":"true",class:[`${t}-drawer`,this.rtlEnabled&&`${t}-drawer--rtl`,`${t}-drawer--${this.placement}-placement`,this.isDragging&&`${t}-drawer--unselectable`,this.nativeScrollbar&&`${t}-drawer--native-scrollbar`]}),[this.resizable?d("div",{class:[`${t}-drawer__resize-trigger`,(this.isDragging||this.isHoverOnResizeTrigger)&&`${t}-drawer__resize-trigger--hover`],onMouseenter:this.handleMouseenterResizeTrigger,onMouseleave:this.handleMouseleaveResizeTrigger,onMousedown:this.handleMousedownResizeTrigger}):null,this.nativeScrollbar?d("div",{class:[`${t}-drawer-content-wrapper`,this.contentClass],style:this.contentStyle,role:"none"},e):d(An,Object.assign({},this.scrollbarProps,{contentStyle:this.contentStyle,contentClass:[`${t}-drawer-content-wrapper`,this.contentClass],theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar}),e)]),this.bodyDirectives)})})),[[Pn,this.displayDirective==="if"||this.displayed||this.show]]):null}}),{cubicBezierEaseIn:au,cubicBezierEaseOut:lu}=en;function su({duration:e="0.3s",leaveDuration:t="0.2s",name:n="slide-in-from-bottom"}={}){return[D(`&.${n}-transition-leave-active`,{transition:`transform ${t} ${au}`}),D(`&.${n}-transition-enter-active`,{transition:`transform ${e} ${lu}`}),D(`&.${n}-transition-enter-to`,{transform:"translateY(0)"}),D(`&.${n}-transition-enter-from`,{transform:"translateY(100%)"}),D(`&.${n}-transition-leave-from`,{transform:"translateY(0)"}),D(`&.${n}-transition-leave-to`,{transform:"translateY(100%)"})]}const{cubicBezierEaseIn:du,cubicBezierEaseOut:cu}=en;function uu({duration:e="0.3s",leaveDuration:t="0.2s",name:n="slide-in-from-left"}={}){return[D(`&.${n}-transition-leave-active`,{transition:`transform ${t} ${du}`}),D(`&.${n}-transition-enter-active`,{transition:`transform ${e} ${cu}`}),D(`&.${n}-transition-enter-to`,{transform:"translateX(0)"}),D(`&.${n}-transition-enter-from`,{transform:"translateX(-100%)"}),D(`&.${n}-transition-leave-from`,{transform:"translateX(0)"}),D(`&.${n}-transition-leave-to`,{transform:"translateX(-100%)"})]}const{cubicBezierEaseIn:fu,cubicBezierEaseOut:hu}=en;function vu({duration:e="0.3s",leaveDuration:t="0.2s",name:n="slide-in-from-right"}={}){return[D(`&.${n}-transition-leave-active`,{transition:`transform ${t} ${fu}`}),D(`&.${n}-transition-enter-active`,{transition:`transform ${e} ${hu}`}),D(`&.${n}-transition-enter-to`,{transform:"translateX(0)"}),D(`&.${n}-transition-enter-from`,{transform:"translateX(100%)"}),D(`&.${n}-transition-leave-from`,{transform:"translateX(0)"}),D(`&.${n}-transition-leave-to`,{transform:"translateX(100%)"})]}const{cubicBezierEaseIn:gu,cubicBezierEaseOut:pu}=en;function bu({duration:e="0.3s",leaveDuration:t="0.2s",name:n="slide-in-from-top"}={}){return[D(`&.${n}-transition-leave-active`,{transition:`transform ${t} ${gu}`}),D(`&.${n}-transition-enter-active`,{transition:`transform ${e} ${pu}`}),D(`&.${n}-transition-enter-to`,{transform:"translateY(0)"}),D(`&.${n}-transition-enter-from`,{transform:"translateY(-100%)"}),D(`&.${n}-transition-leave-from`,{transform:"translateY(0)"}),D(`&.${n}-transition-leave-to`,{transform:"translateY(-100%)"})]}const mu=D([N("drawer",`
 word-break: break-word;
 line-height: var(--n-line-height);
 position: absolute;
 pointer-events: all;
 box-shadow: var(--n-box-shadow);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 background-color: var(--n-color);
 color: var(--n-text-color);
 box-sizing: border-box;
 `,[vu(),uu(),bu(),su(),Z("unselectable",`
 user-select: none; 
 -webkit-user-select: none;
 `),Z("native-scrollbar",[N("drawer-content-wrapper",`
 overflow: auto;
 height: 100%;
 `)]),_("resize-trigger",`
 position: absolute;
 background-color: #0000;
 transition: background-color .3s var(--n-bezier);
 `,[Z("hover",`
 background-color: var(--n-resize-trigger-color-hover);
 `)]),N("drawer-content-wrapper",`
 box-sizing: border-box;
 `),N("drawer-content",`
 height: 100%;
 display: flex;
 flex-direction: column;
 `,[Z("native-scrollbar",[N("drawer-body-content-wrapper",`
 height: 100%;
 overflow: auto;
 `)]),N("drawer-body",`
 flex: 1 0 0;
 overflow: hidden;
 `),N("drawer-body-content-wrapper",`
 box-sizing: border-box;
 padding: var(--n-body-padding);
 `),N("drawer-header",`
 font-weight: var(--n-title-font-weight);
 line-height: 1;
 font-size: var(--n-title-font-size);
 color: var(--n-title-text-color);
 padding: var(--n-header-padding);
 transition: border .3s var(--n-bezier);
 border-bottom: 1px solid var(--n-divider-color);
 border-bottom: var(--n-header-border-bottom);
 display: flex;
 justify-content: space-between;
 align-items: center;
 `,[_("main",`
 flex: 1;
 `),_("close",`
 margin-left: 6px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)]),N("drawer-footer",`
 display: flex;
 justify-content: flex-end;
 border-top: var(--n-footer-border-top);
 transition: border .3s var(--n-bezier);
 padding: var(--n-footer-padding);
 `)]),Z("right-placement",`
 top: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-bottom-left-radius: var(--n-border-radius);
 `,[_("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 left: 0;
 transform: translateX(-1.5px);
 cursor: ew-resize;
 `)]),Z("left-placement",`
 top: 0;
 bottom: 0;
 left: 0;
 border-top-right-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[_("resize-trigger",`
 width: 3px;
 height: 100%;
 top: 0;
 right: 0;
 transform: translateX(1.5px);
 cursor: ew-resize;
 `)]),Z("top-placement",`
 top: 0;
 left: 0;
 right: 0;
 border-bottom-left-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `,[_("resize-trigger",`
 width: 100%;
 height: 3px;
 bottom: 0;
 left: 0;
 transform: translateY(1.5px);
 cursor: ns-resize;
 `)]),Z("bottom-placement",`
 left: 0;
 bottom: 0;
 right: 0;
 border-top-left-radius: var(--n-border-radius);
 border-top-right-radius: var(--n-border-radius);
 `,[_("resize-trigger",`
 width: 100%;
 height: 3px;
 top: 0;
 left: 0;
 transform: translateY(-1.5px);
 cursor: ns-resize;
 `)])]),D("body",[D(">",[N("drawer-container",`
 position: fixed;
 `)])]),N("drawer-container",`
 position: relative;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 pointer-events: none;
 `,[D("> *",`
 pointer-events: all;
 `)]),N("drawer-mask",`
 background-color: rgba(0, 0, 0, .3);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `,[Z("invisible",`
 background-color: rgba(0, 0, 0, 0)
 `),Nr({enterDuration:"0.2s",leaveDuration:"0.2s",enterCubicBezier:"var(--n-bezier-in)",leaveCubicBezier:"var(--n-bezier-out)"})])]),yu=Object.assign(Object.assign({},Be.props),{show:Boolean,width:[Number,String],height:[Number,String],placement:{type:String,default:"right"},maskClosable:{type:Boolean,default:!0},showMask:{type:[Boolean,String],default:!0},to:[String,Object],displayDirective:{type:String,default:"if"},nativeScrollbar:{type:Boolean,default:!0},zIndex:Number,onMaskClick:Function,scrollbarProps:Object,contentClass:String,contentStyle:[Object,String],trapFocus:{type:Boolean,default:!0},onEsc:Function,autoFocus:{type:Boolean,default:!0},closeOnEsc:{type:Boolean,default:!0},blockScroll:{type:Boolean,default:!0},maxWidth:Number,maxHeight:Number,minWidth:Number,minHeight:Number,resizable:Boolean,defaultWidth:{type:[Number,String],default:251},defaultHeight:{type:[Number,String],default:251},onUpdateWidth:[Function,Array],onUpdateHeight:[Function,Array],"onUpdate:width":[Function,Array],"onUpdate:height":[Function,Array],"onUpdate:show":[Function,Array],onUpdateShow:[Function,Array],onAfterEnter:Function,onAfterLeave:Function,drawerStyle:[String,Object],drawerClass:String,target:null,onShow:Function,onHide:Function}),wu=Se({name:"Drawer",inheritAttrs:!1,props:yu,setup(e){const{mergedClsPrefixRef:t,namespaceRef:n,inlineThemeDisabled:o}=ot(e),r=En(),a=Be("Drawer","-drawer",mu,Aa,e,t),l=T(e.defaultWidth),i=T(e.defaultHeight),s=Et(_e(e,"width"),l),c=Et(_e(e,"height"),i),f=H(()=>{const{placement:P}=e;return P==="top"||P==="bottom"?"":fn(s.value)}),u=H(()=>{const{placement:P}=e;return P==="left"||P==="right"?"":fn(c.value)}),p=P=>{const{onUpdateWidth:V,"onUpdate:width":S}=e;V&&ge(V,P),S&&ge(S,P),l.value=P},y=P=>{const{onUpdateHeight:V,"onUpdate:width":S}=e;V&&ge(V,P),S&&ge(S,P),i.value=P},h=H(()=>[{width:f.value,height:u.value},e.drawerStyle||""]);function b(P){const{onMaskClick:V,maskClosable:S}=e;S&&W(!1),V&&V(P)}function w(P){b(P)}const m=cl();function B(P){var V;(V=e.onEsc)===null||V===void 0||V.call(e),e.show&&e.closeOnEsc&&Bl(P)&&(m.value||W(!1))}function W(P){const{onHide:V,onUpdateShow:S,"onUpdate:show":k}=e;S&&ge(S,P),k&&ge(k,P),V&&!P&&ge(V,P)}Ge(Eo,{isMountedRef:r,mergedThemeRef:a,mergedClsPrefixRef:t,doUpdateShow:W,doUpdateHeight:y,doUpdateWidth:p});const F=H(()=>{const{common:{cubicBezierEaseInOut:P,cubicBezierEaseIn:V,cubicBezierEaseOut:S},self:{color:k,textColor:R,boxShadow:K,lineHeight:j,headerPadding:z,footerPadding:G,borderRadius:E,bodyPadding:J,titleFontSize:Q,titleTextColor:X,titleFontWeight:te,headerBorderBottom:ue,footerBorderTop:le,closeIconColor:re,closeIconColorHover:xe,closeIconColorPressed:O,closeColorHover:L,closeColorPressed:pe,closeIconSize:fe,closeSize:Me,closeBorderRadius:Fe,resizableTriggerColorHover:ie}}=a.value;return{"--n-line-height":j,"--n-color":k,"--n-border-radius":E,"--n-text-color":R,"--n-box-shadow":K,"--n-bezier":P,"--n-bezier-out":S,"--n-bezier-in":V,"--n-header-padding":z,"--n-body-padding":J,"--n-footer-padding":G,"--n-title-text-color":X,"--n-title-font-size":Q,"--n-title-font-weight":te,"--n-header-border-bottom":ue,"--n-footer-border-top":le,"--n-close-icon-color":re,"--n-close-icon-color-hover":xe,"--n-close-icon-color-pressed":O,"--n-close-size":Me,"--n-close-color-hover":L,"--n-close-color-pressed":pe,"--n-close-icon-size":fe,"--n-close-border-radius":Fe,"--n-resize-trigger-color-hover":ie}}),C=o?at("drawer",void 0,F,e):void 0;return{mergedClsPrefix:t,namespace:n,mergedBodyStyle:h,handleOutsideClick:w,handleMaskClick:b,handleEsc:B,mergedTheme:a,cssVars:o?void 0:F,themeClass:C==null?void 0:C.themeClass,onRender:C==null?void 0:C.onRender,isMounted:r}},render(){const{mergedClsPrefix:e}=this;return d(Zr,{to:this.to,show:this.show},{default:()=>{var t;return(t=this.onRender)===null||t===void 0||t.call(this),_t(d("div",{class:[`${e}-drawer-container`,this.namespace,this.themeClass],style:this.cssVars,role:"none"},this.showMask?d(Qt,{name:"fade-in-transition",appear:this.isMounted},{default:()=>this.show?d("div",{"aria-hidden":!0,class:[`${e}-drawer-mask`,this.showMask==="transparent"&&`${e}-drawer-mask--invisible`],onClick:this.handleMaskClick}):null}):null,d(iu,Object.assign({},this.$attrs,{class:[this.drawerClass,this.$attrs.class],style:[this.mergedBodyStyle,this.$attrs.style],blockScroll:this.blockScroll,contentStyle:this.contentStyle,contentClass:this.contentClass,placement:this.placement,scrollbarProps:this.scrollbarProps,show:this.show,displayDirective:this.displayDirective,nativeScrollbar:this.nativeScrollbar,onAfterEnter:this.onAfterEnter,onAfterLeave:this.onAfterLeave,trapFocus:this.trapFocus,autoFocus:this.autoFocus,resizable:this.resizable,maxHeight:this.maxHeight,minHeight:this.minHeight,maxWidth:this.maxWidth,minWidth:this.minWidth,showMask:this.showMask,onEsc:this.handleEsc,onClickoutside:this.handleOutsideClick}),this.$slots)),[[Do,{zIndex:this.zIndex,enabled:this.show}]])}})}}),xu={title:String,headerClass:String,headerStyle:[Object,String],footerClass:String,footerStyle:[Object,String],bodyClass:String,bodyStyle:[Object,String],bodyContentClass:String,bodyContentStyle:[Object,String],nativeScrollbar:{type:Boolean,default:!0},scrollbarProps:Object,closable:Boolean},Cu=Se({name:"DrawerContent",props:xu,slots:Object,setup(){const e=We(Eo,null);e||Da("drawer-content","`n-drawer-content` must be placed inside `n-drawer`.");const{doUpdateShow:t}=e;function n(){t(!1)}return{handleCloseClick:n,mergedTheme:e.mergedThemeRef,mergedClsPrefix:e.mergedClsPrefixRef}},render(){const{title:e,mergedClsPrefix:t,nativeScrollbar:n,mergedTheme:o,bodyClass:r,bodyStyle:a,bodyContentClass:l,bodyContentStyle:i,headerClass:s,headerStyle:c,footerClass:f,footerStyle:u,scrollbarProps:p,closable:y,$slots:h}=this;return d("div",{role:"none",class:[`${t}-drawer-content`,n&&`${t}-drawer-content--native-scrollbar`]},h.header||e||y?d("div",{class:[`${t}-drawer-header`,s],style:c,role:"none"},d("div",{class:`${t}-drawer-header__main`,role:"heading","aria-level":"1"},h.header!==void 0?h.header():e),y&&d(Lr,{onClick:this.handleCloseClick,clsPrefix:t,class:`${t}-drawer-header__close`,absolute:!0})):null,n?d("div",{class:[`${t}-drawer-body`,r],style:a,role:"none"},d("div",{class:[`${t}-drawer-body-content-wrapper`,l],style:i,role:"none"},h)):d(An,Object.assign({themeOverrides:o.peerOverrides.Scrollbar,theme:o.peers.Scrollbar},p,{class:`${t}-drawer-body`,contentClass:[`${t}-drawer-body-content-wrapper`,l],contentStyle:i}),h),h.footer?d("div",{class:[`${t}-drawer-footer`,f],style:u,role:"none"},h.footer()):null)}}),Su=D([D("@keyframes spin-rotate",`
 from {
 transform: rotate(0);
 }
 to {
 transform: rotate(360deg);
 }
 `),N("spin-container",`
 position: relative;
 `,[N("spin-body",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[Nr()])]),N("spin-body",`
 display: inline-flex;
 align-items: center;
 justify-content: center;
 flex-direction: column;
 `),N("spin",`
 display: inline-flex;
 height: var(--n-size);
 width: var(--n-size);
 font-size: var(--n-size);
 color: var(--n-color);
 `,[Z("rotate",`
 animation: spin-rotate 2s linear infinite;
 `)]),N("spin-description",`
 display: inline-block;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 margin-top: 8px;
 `),N("spin-content",`
 opacity: 1;
 transition: opacity .3s var(--n-bezier);
 pointer-events: all;
 `,[Z("spinning",`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),ku={small:20,medium:18,large:16},_u=Object.assign(Object.assign(Object.assign({},Be.props),{contentClass:String,contentStyle:[Object,String],description:String,size:{type:[String,Number],default:"medium"},show:{type:Boolean,default:!0},rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number}),Wa),$u=Se({name:"Spin",props:_u,slots:Object,setup(e){const{mergedClsPrefixRef:t,inlineThemeDisabled:n}=ot(e),o=Be("Spin","-spin",Su,La,e,t),r=H(()=>{const{size:s}=e,{common:{cubicBezierEaseInOut:c},self:f}=o.value,{opacitySpinning:u,color:p,textColor:y}=f,h=typeof s=="number"?bt(s):f[q("size",s)];return{"--n-bezier":c,"--n-opacity-spinning":u,"--n-size":h,"--n-color":p,"--n-text-color":y}}),a=n?at("spin",H(()=>{const{size:s}=e;return typeof s=="number"?String(s):s[0]}),r,e):void 0,l=Fo(e,["spinning","show"]),i=T(!1);return Bt(s=>{let c;if(l.value){const{delay:f}=e;if(f){c=window.setTimeout(()=>{i.value=!0},f),s(()=>{clearTimeout(c)});return}}i.value=l.value}),{mergedClsPrefix:t,active:i,mergedStrokeWidth:H(()=>{const{strokeWidth:s}=e;if(s!==void 0)return s;const{size:c}=e;return ku[typeof c=="number"?"medium":c]}),cssVars:n?void 0:r,themeClass:a==null?void 0:a.themeClass,onRender:a==null?void 0:a.onRender}},render(){var e,t;const{$slots:n,mergedClsPrefix:o,description:r}=this,a=n.icon&&this.rotate,l=(r||n.description)&&d("div",{class:`${o}-spin-description`},r||((e=n.description)===null||e===void 0?void 0:e.call(n))),i=n.icon?d("div",{class:[`${o}-spin-body`,this.themeClass]},d("div",{class:[`${o}-spin`,a&&`${o}-spin--rotate`],style:n.default?"":this.cssVars},n.icon()),l):d("div",{class:[`${o}-spin-body`,this.themeClass]},d(vn,{clsPrefix:o,style:n.default?"":this.cssVars,stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,radius:this.radius,scale:this.scale,class:`${o}-spin`}),l);return(t=this.onRender)===null||t===void 0||t.call(this),n.default?d("div",{class:[`${o}-spin-container`,this.themeClass],style:this.cssVars},d("div",{class:[`${o}-spin-content`,this.active&&`${o}-spin-content--spinning`,this.contentClass],style:this.contentStyle},n),d(Qt,{name:"fade-in-transition"},{default:()=>this.active?i:null})):i}}),zu=N("switch",`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[_("children-placeholder",`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),_("rail-placeholder",`
 display: flex;
 flex-wrap: none;
 `),_("button-placeholder",`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),N("base-loading",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[zn({left:"50%",top:"50%",originalTransform:"translateX(-50%) translateY(-50%)"})]),_("checked, unchecked",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 box-sizing: border-box;
 position: absolute;
 white-space: nowrap;
 top: 0;
 bottom: 0;
 display: flex;
 align-items: center;
 line-height: 1;
 `),_("checked",`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),_("unchecked",`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),D("&:focus",[_("rail",`
 box-shadow: var(--n-box-shadow-focus);
 `)]),Z("round",[_("rail","border-radius: calc(var(--n-rail-height) / 2);",[_("button","border-radius: calc(var(--n-button-height) / 2);")])]),De("disabled",[De("icon",[Z("rubber-band",[Z("pressed",[_("rail",[_("button","max-width: var(--n-button-width-pressed);")])]),_("rail",[D("&:active",[_("button","max-width: var(--n-button-width-pressed);")])]),Z("active",[Z("pressed",[_("rail",[_("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])]),_("rail",[D("&:active",[_("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])])])])])]),Z("active",[_("rail",[_("button","left: calc(100% - var(--n-button-width) - var(--n-offset))")])]),_("rail",`
 overflow: hidden;
 height: var(--n-rail-height);
 min-width: var(--n-rail-width);
 border-radius: var(--n-rail-border-radius);
 cursor: pointer;
 position: relative;
 transition:
 opacity .3s var(--n-bezier),
 background .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-rail-color);
 `,[_("button-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 font-size: calc(var(--n-button-height) - 4px);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 display: flex;
 justify-content: center;
 align-items: center;
 line-height: 1;
 `,[zn()]),_("button",`
 align-items: center; 
 top: var(--n-offset);
 left: var(--n-offset);
 height: var(--n-button-height);
 width: var(--n-button-width-pressed);
 max-width: var(--n-button-width);
 border-radius: var(--n-button-border-radius);
 background-color: var(--n-button-color);
 box-shadow: var(--n-button-box-shadow);
 box-sizing: border-box;
 cursor: inherit;
 content: "";
 position: absolute;
 transition:
 background-color .3s var(--n-bezier),
 left .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 `)]),Z("active",[_("rail","background-color: var(--n-rail-color-active);")]),Z("loading",[_("rail",`
 cursor: wait;
 `)]),Z("disabled",[_("rail",`
 cursor: not-allowed;
 opacity: .5;
 `)])]),Pu=Object.assign(Object.assign({},Be.props),{size:String,value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},spinProps:Object,onChange:[Function,Array]});let dn;const Mu=Se({name:"Switch",props:Pu,slots:Object,setup(e){dn===void 0&&(typeof CSS<"u"?typeof CSS.supports<"u"?dn=CSS.supports("width","max(1px)"):dn=!1:dn=!0);const{mergedClsPrefixRef:t,inlineThemeDisabled:n,mergedComponentPropsRef:o}=ot(e),r=Be("Switch","-switch",zu,Na,e,t),a=Dn(e,{mergedSize(k){var R,K;if(e.size!==void 0)return e.size;if(k)return k.mergedSize.value;const j=(K=(R=o==null?void 0:o.value)===null||R===void 0?void 0:R.Switch)===null||K===void 0?void 0:K.size;return j||"medium"}}),{mergedSizeRef:l,mergedDisabledRef:i}=a,s=T(e.defaultValue),c=_e(e,"value"),f=Et(c,s),u=H(()=>f.value===e.checkedValue),p=T(!1),y=T(!1),h=H(()=>{const{railStyle:k}=e;if(k)return k({focused:y.value,checked:u.value})});function b(k){const{"onUpdate:value":R,onChange:K,onUpdateValue:j}=e,{nTriggerFormInput:z,nTriggerFormChange:G}=a;R&&ge(R,k),j&&ge(j,k),K&&ge(K,k),s.value=k,z(),G()}function w(){const{nTriggerFormFocus:k}=a;k()}function m(){const{nTriggerFormBlur:k}=a;k()}function B(){e.loading||i.value||(f.value!==e.checkedValue?b(e.checkedValue):b(e.uncheckedValue))}function W(){y.value=!0,w()}function F(){y.value=!1,m(),p.value=!1}function C(k){e.loading||i.value||k.key===" "&&(f.value!==e.checkedValue?b(e.checkedValue):b(e.uncheckedValue),p.value=!1)}function P(k){e.loading||i.value||k.key===" "&&(k.preventDefault(),p.value=!0)}const V=H(()=>{const{value:k}=l,{self:{opacityDisabled:R,railColor:K,railColorActive:j,buttonBoxShadow:z,buttonColor:G,boxShadowFocus:E,loadingColor:J,textColor:Q,iconColor:X,[q("buttonHeight",k)]:te,[q("buttonWidth",k)]:ue,[q("buttonWidthPressed",k)]:le,[q("railHeight",k)]:re,[q("railWidth",k)]:xe,[q("railBorderRadius",k)]:O,[q("buttonBorderRadius",k)]:L},common:{cubicBezierEaseInOut:pe}}=r.value;let fe,Me,Fe;return dn?(fe=`calc((${re} - ${te}) / 2)`,Me=`max(${re}, ${te})`,Fe=`max(${xe}, calc(${xe} + ${te} - ${re}))`):(fe=bt((et(re)-et(te))/2),Me=bt(Math.max(et(re),et(te))),Fe=et(re)>et(te)?xe:bt(et(xe)+et(te)-et(re))),{"--n-bezier":pe,"--n-button-border-radius":L,"--n-button-box-shadow":z,"--n-button-color":G,"--n-button-width":ue,"--n-button-width-pressed":le,"--n-button-height":te,"--n-height":Me,"--n-offset":fe,"--n-opacity-disabled":R,"--n-rail-border-radius":O,"--n-rail-color":K,"--n-rail-color-active":j,"--n-rail-height":re,"--n-rail-width":xe,"--n-width":Fe,"--n-box-shadow-focus":E,"--n-loading-color":J,"--n-text-color":Q,"--n-icon-color":X}}),S=n?at("switch",H(()=>l.value[0]),V,e):void 0;return{handleClick:B,handleBlur:F,handleFocus:W,handleKeyup:C,handleKeydown:P,mergedRailStyle:h,pressed:p,mergedClsPrefix:t,mergedValue:f,checked:u,mergedDisabled:i,cssVars:n?void 0:V,themeClass:S==null?void 0:S.themeClass,onRender:S==null?void 0:S.onRender}},render(){const{mergedClsPrefix:e,mergedDisabled:t,checked:n,mergedRailStyle:o,onRender:r,$slots:a}=this;r==null||r();const{checked:l,unchecked:i,icon:s,"checked-icon":c,"unchecked-icon":f}=a,u=!(qt(s)&&qt(c)&&qt(f));return d("div",{role:"switch","aria-checked":n,class:[`${e}-switch`,this.themeClass,u&&`${e}-switch--icon`,n&&`${e}-switch--active`,t&&`${e}-switch--disabled`,this.round&&`${e}-switch--round`,this.loading&&`${e}-switch--loading`,this.pressed&&`${e}-switch--pressed`,this.rubberBand&&`${e}-switch--rubber-band`],tabindex:this.mergedDisabled?void 0:0,style:this.cssVars,onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},d("div",{class:`${e}-switch__rail`,"aria-hidden":"true",style:o},Re(l,p=>Re(i,y=>p||y?d("div",{"aria-hidden":!0,class:`${e}-switch__children-placeholder`},d("div",{class:`${e}-switch__rail-placeholder`},d("div",{class:`${e}-switch__button-placeholder`}),p),d("div",{class:`${e}-switch__rail-placeholder`},d("div",{class:`${e}-switch__button-placeholder`}),y)):null)),d("div",{class:`${e}-switch__button`},Re(s,p=>Re(c,y=>Re(f,h=>d(Mo,null,{default:()=>this.loading?d(vn,Object.assign({key:"loading",clsPrefix:e,strokeWidth:20},this.spinProps)):this.checked&&(y||p)?d("div",{class:`${e}-switch__button-icon`,key:y?"checked-icon":"icon"},y||p):!this.checked&&(h||p)?d("div",{class:`${e}-switch__button-icon`,key:h?"unchecked-icon":"icon"},h||p):null})))),Re(l,p=>p&&d("div",{key:"checked",class:`${e}-switch__checked`},p)),Re(i,p=>p&&d("div",{key:"unchecked",class:`${e}-switch__unchecked`},p)))))}}),Tu={class:"gis-page"},Fu={class:"gis-sidebar-head"},Ou=["disabled"],Bu={class:"gis-sidebar-list"},Eu=["disabled","onClick"],Iu={class:"min-w-0 flex-1 text-left"},Ru={class:"gis-session-title"},Au={class:"gis-session-meta"},Du=["title","onClick"],Lu={key:0,class:"gis-sidebar-empty"},Wu={class:"gis-main"},Nu={class:"gis-header"},Vu={class:"mx-auto max-w-3xl px-6 py-4 flex items-center justify-between gap-4"},Hu={class:"flex items-center gap-3.5 min-w-0"},ju={class:"flex items-center gap-2.5 shrink-0"},Ku=["title"],Uu={key:0,viewBox:"0 0 24 24",width:"16",height:"16",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round"},Gu={key:1,viewBox:"0 0 24 24",width:"16",height:"16",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},Xu=["value"],Yu=["disabled"],qu={class:"mx-auto max-w-3xl px-6 py-8 space-y-6"},Zu={key:0,class:"gis-empty animate-enter"},Ju={class:"mt-6 w-full max-w-md text-left space-y-2"},Qu=["onClick"],ef={key:0,class:"gis-msg-row gis-msg-user animate-enter"},tf={class:"gis-user-text"},nf={key:1,class:"gis-msg-row gis-msg-assistant animate-enter"},of={key:0,class:"gis-error w-full"},rf={key:1,class:"space-y-3 w-full"},af={key:0,class:"gis-answer"},lf={class:"whitespace-pre-wrap leading-relaxed text-[14.5px]"},sf={key:1,class:"gis-approval-card animate-enter"},df={class:"flex items-center gap-2.5 min-w-0"},cf={class:"gis-tool-name shrink-0"},uf={class:"gis-tool-args min-w-0"},ff={key:0,class:"mt-2.5 flex items-center gap-2"},hf=["onClick"],vf=["onClick"],gf={key:2,class:"gis-timeline-item gis-tool-inline animate-enter"},pf={class:"gis-timeline-card"},bf={class:"flex items-center gap-2.5 min-w-0"},mf={class:"gis-step-index shrink-0"},yf={class:"gis-tool-name shrink-0"},wf={class:"gis-tool-args min-w-0"},xf={key:0,class:"ml-auto shrink-0 flex items-center gap-1.5 text-muted"},Cf={key:3,class:"gis-artifact"},Sf=["src","alt"],kf={class:"flex items-center justify-between gap-2"},_f={class:"truncate text-xs text-dim font-mono"},$f=["onClick"],zf={key:4,class:"gis-file-row"},Pf={class:"gis-file-ext shrink-0"},Mf={class:"text-sm truncate"},Tf=["onClick"],Ff={class:"font-semibold"},Of={key:0,class:"text-[11px] opacity-80"},Bf={key:1,class:"gis-audit-details"},Ef={class:"mt-1 pl-4 list-disc text-[12px] opacity-90 space-y-0.5"},If={key:1,class:"gis-thinking animate-enter"},Rf={class:"gis-composer"},Af={class:"mx-auto max-w-3xl px-6 py-4"},Df={key:0,class:"mb-2 flex items-center gap-2"},Lf={class:"gis-file-chip"},Wf=["disabled"],Nf={class:"gis-input-row"},Vf={class:"gis-attach-btn",title:"上传数据文件（CSV / GeoJSON / ZIP）"},Hf=["disabled"],jf=["disabled"],Kf={key:0},Uf={key:1,class:"gis-spinner"},Gf={class:"mt-2 flex items-center justify-between text-[11px] text-muted"},Xf={class:"hidden sm:inline"},Yf={class:"gis-settings-body"},qf={class:"gis-settings-sec"},Zf={class:"gis-settings-row"},Jf={class:"mt-3 space-y-1.5"},Qf={class:"gis-model-row"},eh={class:"min-w-0 flex-1"},th={class:"flex items-center gap-1.5"},nh={class:"gis-model-label truncate"},oh={key:0,class:"gis-chip gis-chip-accent"},rh={key:1,class:"gis-chip gis-chip-warn",title:"未配置 API Key"},ih={key:2,class:"gis-chip gis-chip-ok",title:"API Key 已配置"},ah={class:"gis-model-meta truncate"},lh=["title","onClick"],sh=["disabled","title","onClick"],dh={key:0,class:"gis-spinner"},ch={key:1},uh={key:2},fh={key:3},hh=["onClick"],vh={key:0,class:"gis-key-edit"},gh={key:0,class:"gis-model-test-msg"},ph={class:"gis-settings-sec"},bh={class:"gis-settings-row"},mh={class:"gis-settings-sec"},yh={class:"gis-settings-row"},wh=Se({__name:"GisAssistant",setup(e){const t=Ka(),n=ja(),o=async()=>{n.value=!n.value;try{await qn({theme:n.value?"dark":"light"})}catch{}},r=Ua(),a=T(""),l=T(""),i=T(""),s=T(!1),c=T(!1),f=T(""),u=T(""),p=T(null),y=T([]),h=T(!0),b=T("ask"),w=T([]),m=H(()=>a.value.trim().length>0&&!c.value),B=H(()=>w.value.some(I=>I.items.some(g=>g.kind==="tool"&&g.status==="running")));Ie([w,c],async()=>{await mt(),p.value&&(p.value.scrollTop=p.value.scrollHeight)});function W(){requestAnimationFrame(()=>{p.value&&(p.value.scrollTop=p.value.scrollHeight)})}nt(async()=>{var I;C();try{X.value=await Jo(),b.value=((I=X.value)==null?void 0:I.permission_mode)??"ask"}catch{}});function F(I){if(!I)return"";const g=I*1e3,ce=Date.now()-g;if(ce<6e4)return"刚刚";if(ce<36e5)return`${Math.floor(ce/6e4)} 分钟前`;if(ce<864e5)return`${Math.floor(ce/36e5)} 小时前`;const ee=new Date(g);return`${ee.getMonth()+1}/${ee.getDate()}`}async function C(){try{y.value=await Ga()}catch{y.value=[]}}async function P(I){if(!c.value&&!(I.session_id===u.value&&w.value.length))try{const g=await Za(I.session_id);await V(g)}catch{r.error("恢复会话失败")}}async function V(I){var g;u.value=I.session_id,w.value=[];for(const ce of I.rounds){w.value.push({role:"user",content:ce.user,items:[]});const ee=[{kind:"text",content:ce.final}];for(const ne of ce.trajectory)ee.push({kind:"tool",step:ne.step,tool:ne.tool,args:ne.args,result:ne.result,status:ne.result.status==="ok"?"ok":ne.result.status==="error"?"error":"other"});for(const ne of ce.outputs)try{const ke=await Zn(ne,I.session_id);ee.push({kind:"artifact",name:ne,url:ke,ext:ne.toLowerCase().endsWith(".png")?void 0:((g=ne.split(".").pop())==null?void 0:g.toUpperCase())||"FILE"})}catch{}w.value.push({role:"assistant",content:ce.final,items:ee})}await mt(),p.value&&(p.value.scrollTop=p.value.scrollHeight)}async function S(I,g){if(g.stopPropagation(),!c.value)try{await Ja(I.session_id),u.value===I.session_id&&Ke(),await C(),r.success("会话已删除")}catch{r.error("删除失败")}}async function k(I){var ee;const g=I.target,ce=(ee=g.files)==null?void 0:ee[0];if(ce){s.value=!0,f.value="";try{const ne=await Xa(ce);if(!ne.success||!ne.path){f.value=ne.error||"上传失败";return}l.value=ne.path,i.value=ce.name,r.success(`已上传 ${ce.name}`)}catch(ne){f.value=ne instanceof Error?ne.message:String(ne)}finally{s.value=!1,g.value=""}}}function R(){l.value="",i.value=""}function K(I){try{return JSON.stringify(I)}catch{return""}}function j(I){var g;return I.status==="running"?"执行中":I.status==="ok"?"成功":I.status==="error"?String(((g=I.result)==null?void 0:g.error)??"失败"):"完成"}async function z(){if(!m.value)return;c.value=!0,f.value="";const I=a.value.trim();w.value.push({role:"user",content:I,items:[]}),a.value="";const g={role:"assistant",content:"",items:[]};w.value.push(g);const ce=w.value[w.value.length-1];try{await Ya(I,l.value||void 0,u.value||void 0,ee=>G(ce,ee)),r.success("完成")}catch(ee){g.error=ee instanceof Error?ee.message:String(ee)}finally{c.value=!1,await C()}}async function G(I,g){var ce;switch(g.type){case"session_start":u.value=g.session_id;break;case"text_delta":{I.content+=g.delta;const ee=I.items[I.items.length-1];ee&&ee.kind==="text"?ee.content+=g.delta:I.items.push({kind:"text",content:g.delta}),await new Promise(ne=>setTimeout(ne,0));break}case"tool_call":I.items.push({kind:"tool",step:g.step,tool:g.tool,args:g.args,status:"running"});break;case"approval_request":I.items.push({kind:"approval",approvalId:g.approval_id,tool:g.tool,args:g.args??{},status:"pending"});break;case"tool_result":{const ee=I.items.find(ke=>ke.kind==="tool"&&ke.step===g.step&&ke.tool===g.tool&&ke.status==="running");ee&&(ee.result=g.result,ee.status=g.result.status==="ok"?"ok":g.result.status==="error"?"error":"other");const ne=((ce=g.result)==null?void 0:ce.outputs)??[];for(const ke of ne)/\.png$/i.test(ke)&&(I.items.some(A=>A.kind==="artifact"&&A.name===ke)||(async()=>{try{const A=await Zn(ke,u.value);I.items.push({kind:"artifact",name:ke,url:A,ext:void 0}),W()}catch{}})());break}case"done":g.audit_report&&(I.auditReport=g.audit_report);for(const ee of g.outputs)I.items.some(ne=>ne.kind==="artifact"&&ne.name===ee)||(async()=>{var ne;try{const ke=await Zn(ee,u.value);I.items.push({kind:"artifact",name:ee,url:ke,ext:ee.toLowerCase().endsWith(".png")?void 0:((ne=ee.split(".").pop())==null?void 0:ne.toUpperCase())||"FILE"})}catch{}})();setTimeout(W,400);break;case"error":I.error=g.error;break}W()}async function E(I,g){if(!(I.status!=="pending"||!u.value))try{await Qa(u.value,I.approvalId,g),I.status=g==="approve"?"approved":"rejected"}catch(ce){r.error(ce instanceof Error?ce.message:String(ce))}}async function J(I){if(!u.value){b.value=I;return}try{await qa(u.value,I),b.value=I,r.success(`权限模式：${I}`)}catch(g){r.error(g instanceof Error?g.message:String(g))}}const Q=T(!1),X=T(null),te=T([]),ue=T(""),le=T(!1),re=T(null),xe=T(""),O=T(!1),L=T({}),pe=T({});async function fe(){Q.value=!0,await Me()}async function Me(){le.value=!0;try{const[I,g]=await Promise.all([Jo(),el()]);X.value=I,ue.value=I.model_id||g.default,te.value=g.models}catch(I){r.error(`设置加载失败：${I instanceof Error?I.message:String(I)}`)}finally{le.value=!1}}async function Fe(I){ue.value=I;try{await qn({model_id:I}),X.value={...X.value??{},model_id:I},r.success("默认模型已更新，下次对话生效")}catch(g){r.error(g instanceof Error?g.message:String(g)),await Me()}}async function ie(I){try{await qn({permission_mode:I}),X.value={...X.value??{},permission_mode:I},r.success(`默认权限模式：${I}，新会话生效`)}catch(g){r.error(g instanceof Error?g.message:String(g))}}async function Ne(I){try{await tl(I),r.success("模型已删除"),await Me()}catch(g){r.error(g instanceof Error?g.message:String(g))}}async function Le(I){L.value={...L.value,[I]:"testing"};try{const g=await nl(I);L.value={...L.value,[I]:g.ok?"ok":"fail"},pe.value={...pe.value,[I]:g.message||""}}catch(g){L.value={...L.value,[I]:"fail"},pe.value={...pe.value,[I]:String(g)}}}function Ve(I){re.value=I,xe.value=""}async function rt(I){const g=xe.value.trim();if(!g){r.warning("请输入 API Key");return}O.value=!0;try{await ol(I,g),r.success("API Key 已保存"),re.value=null,xe.value="",await Me()}catch(ce){r.error(ce instanceof Error?ce.message:String(ce))}finally{O.value=!1}}function it(){t.push("/gis/models/add")}function Ke(){var I;u.value="",w.value=[],f.value="",l.value="",i.value="",b.value=((I=X.value)==null?void 0:I.permission_mode)??"ask",r.info("已开启新对话")}function Xe(I,g){const ce=document.createElement("a");ce.href=I,ce.download=g,ce.click()}return(I,g)=>{const ce=Xc,ee=ru,ne=tu,ke=Mu,A=$u,Y=Cu,Oe=wu;return de(),se("div",Tu,[g[44]||(g[44]=$("div",{class:"gis-bg","aria-hidden":"true"},[$("div",{class:"gis-bg-grid"}),$("div",{class:"gis-bg-glow"})],-1)),$("aside",{class:Vt(["gis-sidebar",{"gis-sidebar-closed":!h.value}])},[$("div",Fu,[g[7]||(g[7]=$("span",{class:"text-[11px] tracking-[0.2em] text-muted font-semibold"},"会话",-1)),$("button",{class:"gis-sidebar-new",disabled:c.value,onClick:Ke,title:"新会话"},[...g[6]||(g[6]=[$("svg",{viewBox:"0 0 24 24",width:"14",height:"14",fill:"none",stroke:"currentColor","stroke-width":"2.4","stroke-linecap":"round"},[$("path",{d:"M12 5v14M5 12h14"})],-1)])],8,Ou)]),$("div",Bu,[(de(!0),se(je,null,Nt(y.value,he=>(de(),se("button",{key:he.session_id,class:Vt(["gis-session-item",{"gis-session-active":he.session_id===u.value}]),disabled:c.value,onClick:me=>P(he)},[$("div",Iu,[$("p",Ru,Te(he.title),1),$("p",Au,Te(he.rounds)+" 轮 · "+Te(F(he.updated_at)),1)]),$("span",{class:"gis-session-del",title:"删除 "+he.title,onClick:me=>S(he,me)},[...g[8]||(g[8]=[$("svg",{viewBox:"0 0 24 24",width:"12",height:"12",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round"},[$("path",{d:"M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"})],-1)])],8,Du)],10,Eu))),128)),y.value.length?qe("",!0):(de(),se("p",Lu,"暂无历史会话"))])],2),$("div",Wu,[$("header",Nu,[$("div",Vu,[$("div",Hu,[$("button",{class:"gis-sidebar-toggle",onClick:g[0]||(g[0]=he=>h.value=!h.value),title:"切换会话栏"},[...g[9]||(g[9]=[$("svg",{viewBox:"0 0 24 24",width:"16",height:"16",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round"},[$("path",{d:"M3 12h18M3 6h18M3 18h18"})],-1)])]),g[10]||(g[10]=$("div",{class:"gis-seal shrink-0"},"制",-1)),g[11]||(g[11]=$("div",{class:"min-w-0"},[$("h1",{class:"font-display text-lg font-black tracking-tight"},"GIS 智能助手"),$("p",{class:"text-[11px] text-dim mt-0.5 tracking-wide truncate"},"多轮对话 · 工具调用全轨迹可审计")],-1))]),$("div",ju,[$("button",{class:"gis-theme-btn",title:Yn(n)?"切换到亮色":"切换到暗色",onClick:o},[Yn(n)?(de(),se("svg",Uu,[...g[12]||(g[12]=[$("circle",{cx:"12",cy:"12",r:"4"},null,-1),$("path",{d:"M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"},null,-1)])])):(de(),se("svg",Gu,[...g[13]||(g[13]=[$("path",{d:"M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"},null,-1)])]))],8,Ku),$("select",{value:b.value,class:"gis-permission-select",onChange:g[1]||(g[1]=he=>J(he.target.value))},[...g[14]||(g[14]=[$("option",{value:"ask"},"询问审批",-1),$("option",{value:"auto"},"自动执行",-1),$("option",{value:"readonly"},"只读模式",-1)])],40,Xu),$("button",{class:"gis-new-btn",disabled:c.value,onClick:Ke},"↺ 新对话",8,Yu),g[15]||(g[15]=$("span",{class:"gis-status"},[$("span",{class:"gis-status-dot"}),$("span",{class:"hidden sm:inline"},"引擎在线")],-1))])])]),$("main",{ref_key:"chatEl",ref:p,class:"gis-chat"},[$("div",qu,[w.value.length?qe("",!0):(de(),se("div",Zu,[g[17]||(g[17]=$("div",{class:"gis-empty-compass"},"⌖",-1)),g[18]||(g[18]=$("p",{class:"font-display text-lg font-semibold"},"开始你的 GIS 对话",-1)),g[19]||(g[19]=$("p",{class:"text-sm text-muted mt-2 leading-relaxed max-w-md"}," 像和桌面助手聊天一样描述需求：支持多轮连续对话，引擎会记住当前图层与产物， 随时可以继续追问或修改。 ",-1)),$("div",Ju,[g[16]||(g[16]=$("p",{class:"text-[11px] tracking-[0.2em] text-muted"},"示例",-1)),(de(),se(je,null,Nt(["把 gdp_demo.csv 按省份做分级设色图，并导出分级统计 summary.csv","对 gdp_demo.csv 做 0.5 度缓冲区后导出 GeoJSON"],he=>$("button",{key:he,class:"gis-example-chip",onClick:me=>a.value=he},Te(he),9,Qu)),64))])])),(de(!0),se(je,null,Nt(w.value,(he,me)=>{var He;return de(),se(je,{key:me},[he.role==="user"?(de(),se("div",ef,[$("div",tf,Te(he.content),1)])):(de(),se("div",nf,[he.error?(de(),se("div",of,Te(he.error),1)):(de(),se("div",rf,[(de(!0),se(je,null,Nt(he.items,(be,lt)=>(de(),se(je,{key:lt},[be.kind==="text"&&be.content?(de(),se("div",af,[$("p",lf,Te(be.content),1)])):be.kind==="approval"?(de(),se("div",sf,[$("div",df,[g[20]||(g[20]=$("span",{class:"gis-approval-icon"},"⚠",-1)),$("code",cf,Te(be.tool),1),$("span",uf,Te(K(be.args)),1)]),be.status==="pending"?(de(),se("div",ff,[$("button",{class:"gis-approve-btn",onClick:st=>E(be,"approve")},"允许",8,hf),$("button",{class:"gis-reject-btn",onClick:st=>E(be,"reject")},"拒绝",8,vf),g[21]||(g[21]=$("span",{class:"text-xs text-muted"},"危险操作需人工确认",-1))])):(de(),se("div",{key:1,class:Vt(["mt-1.5 text-xs font-medium",be.status==="approved"?"text-emerald-600":"text-rose-600"])},Te(be.status==="approved"?"已允许":"已拒绝"),3))])):be.kind==="tool"?(de(),se("div",gf,[$("span",{class:Vt(["gis-timeline-node",`gis-node-${be.status==="running"?"other":be.status}`])},null,2),$("div",pf,[$("div",bf,[$("span",mf,"#"+Te(be.step),1),$("code",yf,Te(be.tool),1),$("span",wf,Te(K(be.args)),1),be.status==="running"?(de(),se("span",xf,[...g[22]||(g[22]=[$("span",{class:"gis-spinner"},null,-1),$("span",{class:"text-[11px]"},"执行中",-1)])])):(de(),se("span",{key:1,class:Vt(["ml-auto shrink-0",be.status==="ok"?"text-[var(--success)]":be.status==="error"?"text-[var(--danger)]":"text-muted"])},Te(j(be)),3))])])])):be.kind==="artifact"&&!be.ext?(de(),se("figure",Cf,[$("img",{src:be.url,alt:be.name,class:"w-full block",onLoad:W},null,40,Sf),$("figcaption",kf,[$("span",_f,Te(be.name),1),$("a",{class:"gis-download-link shrink-0",onClick:st=>Xe(be.url,be.name)},"下载",8,$f)])])):be.kind==="artifact"?(de(),se("div",zf,[$("span",Pf,Te(be.ext),1),$("span",Mf,Te(be.name),1),$("a",{class:"gis-download-link ml-auto shrink-0",onClick:st=>Xe(be.url,be.name)},"下载",8,Tf)])):qe("",!0)],64))),128)),he.auditReport?(de(),se("div",{key:0,class:Vt(["gis-audit-badge",`gis-audit-${he.auditReport.verdict.toLowerCase()}`])},[g[24]||(g[24]=$("span",{class:"gis-audit-dot"},null,-1)),$("span",Ff,Te(he.auditReport.verdict),1),he.auditReport.verdict!=="PASS"&&he.auditReport.rounds_used?(de(),se("span",Of," · 已尝试修正 "+Te(he.auditReport.rounds_used)+" 轮 ",1)):qe("",!0),he.auditReport.verdict!=="PASS"&&((He=he.auditReport.reasons)!=null&&He.length)?(de(),se("details",Bf,[g[23]||(g[23]=$("summary",{class:"cursor-pointer text-[11px] opacity-80"},"查看原因",-1)),$("ul",Ef,[(de(!0),se(je,null,Nt(he.auditReport.reasons,(be,lt)=>(de(),se("li",{key:lt},Te(be),1))),128))])])):qe("",!0)],2)):qe("",!0)]))]))],64)}),128)),c.value&&!B.value?(de(),se("div",If,[...g[25]||(g[25]=[$("span",{class:"gis-spinner gis-spinner-lg"},null,-1),$("span",{class:"text-sm text-dim"},"正在生成…",-1)])])):qe("",!0)])],512),$("footer",Rf,[$("div",Af,[i.value?(de(),se("div",Df,[$("span",Lf,[Ft(" 📄 "+Te(i.value)+" ",1),$("button",{class:"gis-file-chip-x",disabled:c.value,onClick:R},"×",8,Wf)]),g[26]||(g[26]=$("span",{class:"text-[11px] text-muted"},"该文件将用于本会话",-1))])):qe("",!0),$("div",Nf,[$("label",Vf,[$("input",{type:"file",accept:".csv,.geojson,.json,.zip",class:"hidden",disabled:c.value,onChange:k},null,40,Hf),g[27]||(g[27]=$("svg",{viewBox:"0 0 24 24",width:"18",height:"18",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},[$("path",{d:"M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"})],-1))]),ct(ce,{value:a.value,"onUpdate:value":g[2]||(g[2]=he=>a.value=he),type:"textarea",autosize:{minRows:1,maxRows:6},placeholder:"输入你的 GIS 需求…（Enter 发送，Shift+Enter 换行）",disabled:c.value,onKeydown:Va(Ha(z,["exact","prevent"]),["enter"])},null,8,["value","disabled","onKeydown"]),$("button",{class:"gis-send-btn",disabled:!m.value,title:"发送",onClick:z},[c.value?(de(),se("span",Uf)):(de(),se("span",Kf,[...g[28]||(g[28]=[$("svg",{viewBox:"0 0 24 24",width:"16",height:"16",fill:"currentColor"},[$("path",{d:"M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"})],-1)])]))],8,jf)]),$("div",Gf,[g[29]||(g[29]=$("span",null,"📎 可上传数据 · 未上传时自动使用演示数据",-1)),$("span",Xf,Te(u.value?"多轮对话中 · 图层与产物已保留":"新会话"),1)])])])]),ct(Oe,{show:Q.value,"onUpdate:show":g[5]||(g[5]=he=>Q.value=he),placement:"right",width:380,"trap-focus":!1,class:"gis-settings-drawer"},{default:Mt(()=>[ct(Y,{title:"设置",closable:""},{default:Mt(()=>[ct(A,{show:le.value},{default:Mt(()=>{var he;return[$("div",Yf,[$("section",qf,[g[34]||(g[34]=$("h3",{class:"gis-settings-title"},"模型",-1)),g[35]||(g[35]=$("p",{class:"gis-settings-desc"},"默认模型 · 自定义接入（含本地 Ollama）",-1)),$("div",Zf,[g[30]||(g[30]=$("span",{class:"gis-settings-label"},"默认模型",-1)),ct(ee,{value:ue.value,options:te.value.map(me=>({label:me.is_custom?`${me.label}（自定义）`:me.label,value:me.id})),size:"small",class:"gis-settings-select","onUpdate:value":Fe},null,8,["value","options"])]),$("div",Jf,[(de(!0),se(je,null,Nt(te.value,me=>(de(),se(je,{key:me.id},[$("div",Qf,[$("div",eh,[$("div",th,[$("span",nh,Te(me.label),1),me.is_custom?(de(),se("span",oh,"自定义")):qe("",!0),me.requires_key&&!me.has_key?(de(),se("span",rh,"缺 Key")):me.has_key?(de(),se("span",ih,"Key ✓")):qe("",!0)]),$("p",ah,Te(me.base_url),1)]),me.requires_key||me.has_key?(de(),se("button",{key:0,class:"gis-model-test",title:re.value===me.id?"关闭输入":"配置 / 修改 API Key",onClick:He=>re.value===me.id?re.value=null:Ve(me.id)},Te(re.value===me.id?"收起":"配置 Key"),9,lh)):qe("",!0),$("button",{class:"gis-model-test",disabled:L.value[me.id]==="testing",title:pe.value[me.id],onClick:He=>Le(me.id)},[L.value[me.id]==="testing"?(de(),se("span",dh)):L.value[me.id]==="ok"?(de(),se("span",ch,"测试通过")):L.value[me.id]==="fail"?(de(),se("span",uh,"测试失败")):(de(),se("span",fh,"测试"))],8,sh),me.is_custom?(de(),se("button",{key:1,class:"gis-model-del",title:"删除该模型",onClick:He=>Ne(me.id)},[...g[31]||(g[31]=[$("svg",{viewBox:"0 0 24 24",width:"12",height:"12",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round"},[$("path",{d:"M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"})],-1)])],8,hh)):qe("",!0)]),re.value===me.id?(de(),se("div",vh,[ct(ce,{value:xe.value,"onUpdate:value":g[3]||(g[3]=He=>xe.value=He),type:"password","show-password-on":"click",placeholder:"输入 API Key",size:"small",class:"flex-1"},null,8,["value"]),ct(ne,{size:"tiny",type:"primary",loading:O.value,onClick:He=>rt(me.id)},{default:Mt(()=>[...g[32]||(g[32]=[Ft(" 保存 ",-1)])]),_:1},8,["loading","onClick"]),ct(ne,{size:"tiny",onClick:g[4]||(g[4]=He=>{re.value=null,xe.value=""})},{default:Mt(()=>[...g[33]||(g[33]=[Ft("取消",-1)])]),_:1})])):qe("",!0)],64))),128))]),pe.value[ue.value]?(de(),se("div",gh,Te(pe.value[ue.value]),1)):qe("",!0),$("button",{class:"gis-add-model-btn",title:"前往独立页面添加模型（预置常见厂商，只需填 API Key）",onClick:it}," + 添加模型（新页面） ")]),$("section",ph,[g[39]||(g[39]=$("h3",{class:"gis-settings-title"},"外观",-1)),$("div",bh,[g[38]||(g[38]=$("span",{class:"gis-settings-label"},"主题",-1)),ct(ke,{value:Yn(n),size:"small","onUpdate:value":o},{checked:Mt(()=>[...g[36]||(g[36]=[Ft("暗色",-1)])]),unchecked:Mt(()=>[...g[37]||(g[37]=[Ft("亮色",-1)])]),_:1},8,["value"])])]),$("section",mh,[g[41]||(g[41]=$("h3",{class:"gis-settings-title"},"偏好",-1)),g[42]||(g[42]=$("p",{class:"gis-settings-desc"},"会话默认权限模式（新会话生效，顶栏可临时切换）",-1)),$("div",yh,[g[40]||(g[40]=$("span",{class:"gis-settings-label"},"默认权限",-1)),ct(ee,{value:((he=X.value)==null?void 0:he.permission_mode)??"ask",options:[{label:"询问审批",value:"ask"},{label:"自动执行",value:"auto"},{label:"只读模式",value:"readonly"}],size:"small",class:"gis-settings-select","onUpdate:value":ie},null,8,["value"])])])])]}),_:1},8,["show"])]),_:1})]),_:1},8,["show"]),$("button",{class:"gis-settings-fab",title:"设置",onClick:fe},[...g[43]||(g[43]=[$("svg",{viewBox:"0 0 24 24",width:"18",height:"18",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},[$("circle",{cx:"12",cy:"12",r:"3"}),$("path",{d:"M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"})],-1)])])])}}}),Sh=rl(wh,[["__scopeId","data-v-32b837b7"]]);export{Sh as default};
