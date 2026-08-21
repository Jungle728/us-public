(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))n(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const r of o.addedNodes)r.tagName==="LINK"&&r.rel==="modulepreload"&&n(r)}).observe(document,{childList:!0,subtree:!0});function a(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function n(s){if(s.ep)return;s.ep=!0;const o=a(s);fetch(s.href,o)}})();const ve="modulepreload",fe=function(e){return"/modern/"+e},oe={},be=function(t,a,n){let s=Promise.resolve();if(a&&a.length>0){let r=function(h){return Promise.all(h.map(v=>Promise.resolve(v).then(f=>({status:"fulfilled",value:f}),f=>({status:"rejected",reason:f}))))};document.getElementsByTagName("link");const c=document.querySelector("meta[property=csp-nonce]"),m=(c==null?void 0:c.nonce)||(c==null?void 0:c.getAttribute("nonce"));s=r(a.map(h=>{if(h=fe(h),h in oe)return;oe[h]=!0;const v=h.endsWith(".css"),f=v?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${h}"]${f}`))return;const p=document.createElement("link");if(p.rel=v?"stylesheet":ve,v||(p.as="script"),p.crossOrigin="",p.href=h,m&&p.setAttribute("nonce",m),document.head.appendChild(p),v)return new Promise((g,E)=>{p.addEventListener("load",g),p.addEventListener("error",()=>E(new Error(`Unable to preload CSS for ${h}`)))})}))}function o(r){const c=new Event("vite:preloadError",{cancelable:!0});if(c.payload=r,window.dispatchEvent(c),!c.defaultPrevented)throw r}return s.then(r=>{for(const c of r||[])c.status==="rejected"&&o(c.reason);return t().catch(o)})};/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const de=(e,t,a=[])=>{const n=document.createElementNS("http://www.w3.org/2000/svg",e);return Object.keys(t).forEach(s=>{n.setAttribute(s,String(t[s]))}),a.length&&a.forEach(s=>{const o=de(...s);n.appendChild(o)}),n};var ge=([e,t,a])=>de(e,t,a);/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ye=e=>Array.from(e.attributes).reduce((t,a)=>(t[a.name]=a.value,t),{}),we=e=>typeof e=="string"?e:!e||!e.class?"":e.class&&typeof e.class=="string"?e.class.split(" "):e.class&&Array.isArray(e.class)?e.class:"",$e=e=>e.flatMap(we).map(a=>a.trim()).filter(Boolean).filter((a,n,s)=>s.indexOf(a)===n).join(" "),Me=e=>e.replace(/(\w)(\w*)(_|-|\s*)/g,(t,a,n)=>a.toUpperCase()+n.toLowerCase()),ie=(e,{nameAttr:t,icons:a,attrs:n})=>{var E;const s=e.getAttribute(t);if(s==null)return;const o=Me(s),r=a[o];if(!r)return console.warn(`${e.outerHTML} icon name was not found in the provided icons object.`);const c=ye(e),[m,h,v]=r,f={...h,"data-lucide":s,...n,...c},p=$e(["lucide",`lucide-${s}`,c,n]);p&&Object.assign(f,{class:p});const g=ge([m,f,v]);return(E=e.parentNode)==null?void 0:E.replaceChild(g,e)};/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xe=["svg",l,[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Se=["svg",l,[["path",{d:"M12 17V3"}],["path",{d:"m6 11 6 6 6-6"}],["path",{d:"M19 21H5"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ce=["svg",l,[["path",{d:"m18 9-6-6-6 6"}],["path",{d:"M12 3v14"}],["path",{d:"M5 21h14"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ee=["svg",l,[["path",{d:"M20 6 9 17l-5-5"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ke=["svg",l,[["path",{d:"m9 18 6-6-6-6"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ae=["svg",l,[["path",{d:"M15.6 2.7a10 10 0 1 0 5.7 5.7"}],["circle",{cx:"12",cy:"12",r:"2"}],["path",{d:"M13.4 10.6 19 5"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Le=["svg",l,[["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Te=["svg",l,[["rect",{width:"16",height:"16",x:"4",y:"4",rx:"2"}],["rect",{width:"6",height:"6",x:"9",y:"9",rx:"1"}],["path",{d:"M15 2v2"}],["path",{d:"M15 20v2"}],["path",{d:"M2 15h2"}],["path",{d:"M2 9h2"}],["path",{d:"M20 15h2"}],["path",{d:"M20 9h2"}],["path",{d:"M9 2v2"}],["path",{d:"M9 20v2"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const qe=["svg",l,[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 12a9 3 0 0 0 5 2.69"}],["path",{d:"M21 9.3V5"}],["path",{d:"M3 5v14a9 3 0 0 0 6.47 2.88"}],["path",{d:"M12 12v4h4"}],["path",{d:"M13 20a5 5 0 0 0 9-3 4.5 4.5 0 0 0-4.5-4.5c-1.33 0-2.54.54-3.41 1.41L12 16"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Re=["svg",l,[["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["polyline",{points:"7 10 12 15 17 10"}],["line",{x1:"12",x2:"12",y1:"15",y2:"3"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ie=["svg",l,[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Pe=["svg",l,[["path",{d:"M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"}],["path",{d:"M14.084 14.158a3 3 0 0 1-4.242-4.242"}],["path",{d:"M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ne=["svg",l,[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Oe=["svg",l,[["path",{d:"M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"}],["path",{d:"M14 2v4a2 2 0 0 0 2 2h4"}],["path",{d:"M10 12a1 1 0 0 0-1 1v1a1 1 0 0 1-1 1 1 1 0 0 1 1 1v1a1 1 0 0 0 1 1"}],["path",{d:"M14 18a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1 1 1 0 0 1-1-1v-1a1 1 0 0 0-1-1"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ue=["svg",l,[["line",{x1:"22",x2:"2",y1:"12",y2:"12"}],["path",{d:"M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"}],["line",{x1:"6",x2:"6.01",y1:"16",y2:"16"}],["line",{x1:"10",x2:"10.01",y1:"16",y2:"16"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const He=["svg",l,[["path",{d:"M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"}],["circle",{cx:"16.5",cy:"7.5",r:".5",fill:"currentColor"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const je=["svg",l,[["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}],["polyline",{points:"16 17 21 12 16 7"}],["line",{x1:"21",x2:"9",y1:"12",y2:"12"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const De=["svg",l,[["path",{d:"M6 19v-3"}],["path",{d:"M10 19v-3"}],["path",{d:"M14 19v-3"}],["path",{d:"M18 19v-3"}],["path",{d:"M8 11V9"}],["path",{d:"M16 11V9"}],["path",{d:"M12 11V9"}],["path",{d:"M2 15h20"}],["path",{d:"M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v1.1a2 2 0 0 0 0 3.837V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5.1a2 2 0 0 0 0-3.837Z"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ve=["svg",l,[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Be=["svg",l,[["rect",{x:"16",y:"16",width:"6",height:"6",rx:"1"}],["rect",{x:"2",y:"16",width:"6",height:"6",rx:"1"}],["rect",{x:"9",y:"2",width:"6",height:"6",rx:"1"}],["path",{d:"M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"}],["path",{d:"M12 12V8"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fe=["svg",l,[["path",{d:"M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"}],["path",{d:"m15 5 4 4"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _e=["svg",l,[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ze=["svg",l,[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ke=["svg",l,[["path",{d:"M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const We=["svg",l,[["circle",{cx:"6",cy:"19",r:"3"}],["path",{d:"M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"}],["circle",{cx:"18",cy:"5",r:"3"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ze=["svg",l,[["circle",{cx:"11",cy:"11",r:"8"}],["path",{d:"m21 21-4.3-4.3"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ge=["svg",l,[["rect",{width:"20",height:"8",x:"2",y:"2",rx:"2",ry:"2"}],["rect",{width:"20",height:"8",x:"2",y:"14",rx:"2",ry:"2"}],["line",{x1:"6",x2:"6.01",y1:"6",y2:"6"}],["line",{x1:"6",x2:"6.01",y1:"18",y2:"18"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Je=["svg",l,[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}],["path",{d:"m9 12 2 2 4-4"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xe=["svg",l,[["circle",{cx:"12",cy:"12",r:"4"}],["path",{d:"M12 2v2"}],["path",{d:"M12 20v2"}],["path",{d:"m4.93 4.93 1.41 1.41"}],["path",{d:"m17.66 17.66 1.41 1.41"}],["path",{d:"M2 12h2"}],["path",{d:"M20 12h2"}],["path",{d:"m6.34 17.66-1.41 1.41"}],["path",{d:"m19.07 4.93-1.41 1.41"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Qe=["svg",l,[["polyline",{points:"4 17 10 11 4 5"}],["line",{x1:"12",x2:"20",y1:"19",y2:"19"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ye=["svg",l,[["path",{d:"M3 6h18"}],["path",{d:"M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"}],["path",{d:"M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"}],["line",{x1:"10",x2:"10",y1:"11",y2:"17"}],["line",{x1:"14",x2:"14",y1:"11",y2:"17"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const et=["svg",l,[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["circle",{cx:"9",cy:"7",r:"4"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const tt=["svg",l,[["path",{d:"M12 20h.01"}],["path",{d:"M8.5 16.429a5 5 0 0 1 7 0"}],["path",{d:"M5 12.859a10 10 0 0 1 5.17-2.69"}],["path",{d:"M19 12.859a10 10 0 0 0-2.007-1.523"}],["path",{d:"M2 8.82a15 15 0 0 1 4.177-2.643"}],["path",{d:"M22 8.82a15 15 0 0 0-11.288-3.764"}],["path",{d:"m2 2 20 20"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const at=["svg",l,[["path",{d:"M12 20h.01"}],["path",{d:"M2 8.82a15 15 0 0 1 20 0"}],["path",{d:"M5 12.859a10 10 0 0 1 14 0"}],["path",{d:"M8.5 16.429a5 5 0 0 1 7 0"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const nt=["svg",l,[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]]];/**
 * @license lucide v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const st=({icons:e={},nameAttr:t="data-lucide",attrs:a={}}={})=>{if(!Object.values(e).length)throw new Error(`Please provide an icons object.
If you want to use all the icons you can import it like:
 \`import { createIcons, icons } from 'lucide';
lucide.createIcons({icons});\``);if(typeof document>"u")throw new Error("`createIcons()` only works in a browser environment.");const n=document.querySelectorAll(`[${t}]`);if(Array.from(n).forEach(s=>ie(s,{nameAttr:t,icons:e,attrs:a})),t==="data-lucide"){const s=document.querySelectorAll("[icon-name]");s.length>0&&(console.warn("[Lucide] Some icons were found with the now deprecated icon-name attribute. These will still be replaced for backwards compatibility, but will no longer be supported in v1.0 and you should switch to data-lucide"),Array.from(s).forEach(o=>ie(o,{nameAttr:"icon-name",icons:e,attrs:a})))}},ot="/app/api";class D extends Error{}async function it(e){const t=e.headers.get("content-type")||"";if(e.redirected||!t.includes("application/json"))throw new D("Session expired");const a=await e.json();if(!a.success&&a.msg==="Invalid login")throw new D(a.msg);return a}async function x(e,t){const a=await fetch(`${ot}/${e}`,{credentials:"same-origin",headers:{"X-Requested-With":"XMLHttpRequest",...(t==null?void 0:t.headers)||{}},...t}),n=await it(a);if(!n.success)throw new Error(n.msg||"Request failed");return n.obj}function re(e){const t=new URLSearchParams;return Object.entries(e).forEach(([a,n])=>{n!==void 0&&t.set(a,n)}),t}const y={async login(e,t){await x("login",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"},body:re({user:e,pass:t})})},async logout(){await x("logout")},async load(){return x("load")},async loadClient(e){var a;const t=await x(`clients?id=${e}`);if(!((a=t.clients)!=null&&a[0]))throw new Error("Client not found");return t.clients[0]},async status(){return x("status?r=cpu,mem,dsk,net,sys,sbd,db")},async logs(e=80,t="info"){return x(`logs?c=${e}&l=${encodeURIComponent(t)}`)},async saveClient(e,t){await x("save",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"},body:re({object:"clients",action:e,data:JSON.stringify(t,null,2)})})},async restartCore(){await x("restartSb",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"},body:new URLSearchParams})}},O=document.querySelector("#app");if(!O)throw new Error("Application root not found");const rt={Activity:xe,ArrowDownToLine:Se,ArrowUpFromLine:Ce,Check:Ee,ChevronRight:ke,CircleGauge:Ae,Copy:Le,Cpu:Te,DatabaseBackup:qe,Download:Re,ExternalLink:Ie,Eye:Ne,EyeOff:Pe,FileJson:Oe,HardDrive:Ue,KeyRound:He,LogOut:je,MemoryStick:De,Moon:Ve,Network:Be,Pencil:Fe,Plus:_e,RefreshCw:ze,RotateCw:Ke,Route:We,Search:Ze,Server:Ge,ShieldCheck:Je,Sun:Xe,Terminal:Qe,Trash2:Ye,Users:et,Wifi:at,WifiOff:tt,X:nt},I={dashboard:{label:"总览",title:"运行总览",icon:"circle-gauge"},clients:{label:"用户",title:"用户与订阅",icon:"users"},inbounds:{label:"协议",title:"入口协议",icon:"network"},operations:{label:"运维",title:"系统运维",icon:"terminal"}};let i=null,u={},M=ue(),L=!1,V=!0,P;function d(e){return String(e??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;")}function q(){st({icons:rt,attrs:{"aria-hidden":"true",width:18,height:18,"stroke-width":1.8}})}function ue(){const e=window.location.hash.replace(/^#\/?/,"");return e in I?e:"dashboard"}function B(e){document.documentElement.dataset.theme=e,localStorage.setItem("aaitr-theme",e)}function lt(){const e=localStorage.getItem("aaitr-theme");B(e==="light"||e==="dark"?e:window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light")}function $(e=0,t=1){if(!Number.isFinite(e)||e<=0)return"0 B";const a=["B","KiB","MiB","GiB","TiB"],n=Math.min(Math.floor(Math.log(e)/Math.log(1024)),a.length-1);return`${(e/1024**n).toFixed(n===0?0:t)} ${a[n]}`}function _(e=0,t=!1){return e?new Intl.DateTimeFormat("zh-CN",{year:"numeric",month:"2-digit",day:"2-digit",...t?{hour:"2-digit",minute:"2-digit"}:{}}).format(new Date(e*1e3)):"不限"}function pe(e=0){return e<60?`${Math.floor(e)} 秒`:e<3600?`${Math.floor(e/60)} 分钟`:e<86400?`${Math.floor(e/3600)} 小时`:`${Math.floor(e/86400)} 天`}function R(e=0,t=0){return t?Math.max(0,Math.min(100,e/t*100)):0}function F(e,t=""){return e==="vless"&&t.includes("reality")?"VLESS Reality":e==="hysteria2"?"Hysteria2":e==="anytls"?"AnyTLS":e==="shadowsocks"?"Shadowsocks 2022":e==="socks"?"SOCKS5":e==="http"&&t.includes("https")?"HTTPS":e.toUpperCase()}function ct(e){return e.includes("reality")||e.includes("hysteria")||e.includes("anytls")||e.includes("shadowsocks")?"加密节点":e.includes("socks")||e.includes("http")||e.includes("https")?"转发代理":"其他入口"}function b(e,t="success"){var n;(n=document.querySelector(".toast"))==null||n.remove();const a=document.createElement("div");a.className=`toast toast-${t}`,a.innerHTML=`<i data-lucide="${t==="success"?"check":"x"}"></i><span>${d(e)}</span>`,document.body.appendChild(a),q(),window.setTimeout(()=>a.remove(),3600)}function dt(){O.innerHTML=`
    <main class="boot-screen">
      <div class="brand-mark"><span>AA</span></div>
      <div class="boot-copy"><strong>AaITR Console</strong><span>正在连接管理服务</span></div>
      <div class="boot-progress"><span></span></div>
    </main>`}function N(e=""){var a;document.title="登录 · AaITR Console",O.innerHTML=`
    <main class="login-layout">
      <section class="login-brand">
        <div class="brand-lockup"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
        <div class="login-status">
          <div class="status-orbit"><i data-lucide="route"></i></div>
          <p>线路管理</p>
          <strong>CStoneCloud <span>→</span> AaITR</strong>
          <div class="login-tags"><span>Reality</span><span>Hysteria2</span></div>
        </div>
        <small>Private operations surface</small>
      </section>
      <section class="login-panel">
        <form id="login-form" class="login-form" autocomplete="on">
          <div class="mobile-brand"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
          <div class="form-heading"><span>管理后台</span><h1>欢迎回来</h1></div>
          ${e?`<div class="form-error">${d(e)}</div>`:""}
          <label class="field"><span>用户名</span><input name="user" autocomplete="username" required autofocus /></label>
          <label class="field password-field"><span>密码</span><input name="pass" type="password" autocomplete="current-password" required /><button type="button" class="icon-btn password-toggle" title="显示密码"><i data-lucide="eye"></i></button></label>
          <button class="primary-btn login-submit" type="submit"><span>登录</span><i data-lucide="chevron-right"></i></button>
        </form>
      </section>
    </main>`,q();const t=document.querySelector("#login-form");t==null||t.addEventListener("submit",async n=>{n.preventDefault();const s=t.querySelector("button[type=submit]"),o=new FormData(t);s==null||s.setAttribute("disabled","true"),s&&(s.innerHTML='<span>正在登录</span><i class="spin" data-lucide="refresh-cw"></i>'),q();try{await y.login(String(o.get("user")||""),String(o.get("pass")||"")),L=!0,await C(),me()}catch(r){N(r instanceof Error?r.message:"登录失败")}}),(a=document.querySelector(".password-toggle"))==null||a.addEventListener("click",n=>{const s=n.currentTarget,o=document.querySelector('input[name="pass"]');if(!o)return;const r=o.type==="text";o.type=r?"password":"text",s.innerHTML=`<i data-lucide="${r?"eye":"eye-off"}"></i>`,s.title=r?"显示密码":"隐藏密码",q()})}function S(e){const t=I[e];return`<a href="#/${e}" class="nav-item ${M===e?"active":""}" data-route="${e}"><i data-lucide="${t.icon}"></i><span>${t.label}</span></a>`}function z(){var a,n;if(!i)return;const e=document.documentElement.dataset.theme||"light",t=!!((a=u.sbd)!=null&&a.running);document.title=`${I[M].title} · AaITR Console`,O.innerHTML=`
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand-lockup"><div class="brand-mark"><span>AA</span></div><span>AaITR Console</span></div>
        <nav>${S("dashboard")}${S("clients")}${S("inbounds")}${S("operations")}</nav>
        <div class="sidebar-foot">
          <div class="core-chip"><span class="status-dot ${t?"online":"offline"}"></span><div><strong>${t?"Core online":"Core offline"}</strong><small>sing-box ${d(((n=u.sys)==null?void 0:n.appVersion)||"")}</small></div></div>
          <a href="/app/" class="legacy-link"><i data-lucide="external-link"></i><span>高级配置</span></a>
        </div>
      </aside>
      <div class="workspace">
        <header class="topbar">
          <div><span class="eyebrow">AaITR / ${I[M].label}</span><h1>${I[M].title}</h1></div>
          <div class="topbar-actions">
            <button class="icon-btn" id="refresh-button" title="刷新"><i data-lucide="refresh-cw"></i></button>
            <button class="icon-btn" id="theme-button" title="切换外观"><i data-lucide="${e==="dark"?"sun":"moon"}"></i></button>
            <button class="icon-btn" id="logout-button" title="退出登录"><i data-lucide="log-out"></i></button>
          </div>
        </header>
        <main class="content">${ut()}</main>
        <nav class="mobile-nav">${S("dashboard")}${S("clients")}${S("inbounds")}${S("operations")}</nav>
      </div>
    </div>`,q(),yt()}function ut(){switch(M){case"clients":return mt();case"inbounds":return ft();case"operations":return gt();default:return pt()}}function k(e,t,a,n,s){return`<article class="metric-card"><div class="metric-head"><span class="metric-icon"><i data-lucide="${e}"></i></span><span>${t}</span></div><strong>${a}</strong><small>${n}</small>${s===void 0?"":`<div class="meter"><span style="width:${s.toFixed(1)}%"></span></div>`}</article>`}function pt(){var r,c,m,h,v,f,p,g,E,W,Z,G,J,X,Q,Y,ee,te,ae,ne,se;if(!i)return"";const e=i.clients||[],t=((c=(r=i.onlines)==null?void 0:r.user)==null?void 0:c.length)||0,a=e.reduce((w,T)=>w+T.up+T.down,0),n=e.filter(w=>w.enable).length,s=[...e].sort((w,T)=>(T.onlineAt||0)-(w.onlineAt||0)).slice(0,5),o=((h=(m=u.sbd)==null?void 0:m.stats)==null?void 0:h.Uptime)||0;return`
    <section class="metrics-grid">
      ${k("activity","核心状态",(v=u.sbd)!=null&&v.running?"运行中":"已停止",`连续运行 ${pe(o)}`)}
      ${k("users","在线用户",`${t}`,`${n} 个启用账户`)}
      ${k("memory-stick","内存",`${R((f=u.mem)==null?void 0:f.current,(p=u.mem)==null?void 0:p.total).toFixed(0)}%`,`${$((g=u.mem)==null?void 0:g.current)} / ${$((E=u.mem)==null?void 0:E.total)}`,R((W=u.mem)==null?void 0:W.current,(Z=u.mem)==null?void 0:Z.total))}
      ${k("arrow-down-to-line","累计流量",$(a),`上传 ${$(e.reduce((w,T)=>w+T.up,0))}`)}
    </section>
    <section class="dashboard-grid">
      <article class="panel route-panel">
        <div class="section-head"><div><span class="eyebrow">Traffic routes</span><h2>三种出口模式</h2></div><span class="quiet-badge">${i.inbounds.filter(w=>["vless","hysteria2"].includes(w.type)).length} 个协议入口</span></div>
        <div class="route-list">
          ${H("CS","CStoneCloud → AaITR","家宽出口","默认","route-blue")}
          ${H("CSE","CStoneCloud Exit","机房出口","备用","route-amber")}
          ${H("AA","AaITR Exit","家宽直连","对照","route-green")}
        </div>
      </article>
      <article class="panel system-panel">
        <div class="section-head"><div><span class="eyebrow">Server</span><h2>资源状态</h2></div><span class="status-pill ${(G=u.sbd)!=null&&G.running?"ok":"error"}">${(J=u.sbd)!=null&&J.running?"健康":"异常"}</span></div>
        ${j("CPU",u.cpu||0,`${(u.cpu||0).toFixed(1)}%`)}
        ${j("内存",R((X=u.mem)==null?void 0:X.current,(Q=u.mem)==null?void 0:Q.total),$((Y=u.mem)==null?void 0:Y.current))}
        ${j("磁盘",R((ee=u.dsk)==null?void 0:ee.current,(te=u.dsk)==null?void 0:te.total),$((ae=u.dsk)==null?void 0:ae.current))}
        <div class="system-meta"><span>${d(((ne=u.sys)==null?void 0:ne.cpuType)||"Unknown CPU")}</span><span>${((se=u.sys)==null?void 0:se.cpuCount)||0} vCPU</span></div>
      </article>
      <article class="panel recent-panel">
        <div class="section-head"><div><span class="eyebrow">Clients</span><h2>最近活动</h2></div><button class="text-btn" data-go="clients">查看全部<i data-lucide="chevron-right"></i></button></div>
        <div class="recent-list">${s.map(ht).join("")||'<div class="empty-state">暂无用户</div>'}</div>
      </article>
    </section>`}function H(e,t,a,n,s){return`<div class="route-row"><span class="route-code ${s}">${e}</span><div><strong>${t}</strong><small>${a}</small></div><span class="quiet-badge">${n}</span></div>`}function j(e,t,a){return`<div class="resource-row"><div><span>${e}</span><strong>${a}</strong></div><div class="meter"><span style="width:${Math.min(100,t).toFixed(1)}%"></span></div></div>`}function ht(e){var a,n;const t=(n=(a=i==null?void 0:i.onlines)==null?void 0:a.user)==null?void 0:n.includes(e.name);return`<div class="recent-row"><span class="avatar">${d(e.name.slice(0,2).toUpperCase())}</span><div><strong>${d(e.name)}</strong><small>${d(e.group||"未分组")}</small></div><span class="last-seen"><span class="status-dot ${t?"online":""}"></span>${t?"在线":_(e.onlineAt,!0)}</span></div>`}function mt(){var t,a;return i?`
    <section class="toolbar panel-flat">
      <div class="search-box"><i data-lucide="search"></i><input id="client-search" placeholder="搜索名称、备注或分组" /></div>
      <select id="client-group-filter" aria-label="按分组筛选"><option value="">全部分组</option>${[...new Set(i.clients.map(n=>n.group).filter(Boolean))].map(n=>`<option value="${d(n)}">${d(n)}</option>`).join("")}</select>
      <select id="client-state-filter" aria-label="按状态筛选"><option value="">全部状态</option><option value="online">在线</option><option value="enabled">已启用</option><option value="disabled">已停用</option><option value="expired">已过期</option></select>
      <button class="primary-btn" id="add-client" aria-label="新建用户" title="新建用户"><i data-lucide="plus"></i><span>新建用户</span></button>
    </section>
    <section class="panel table-panel">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>用户</th><th>状态</th><th>用量</th><th>到期</th><th>入口</th><th class="align-right">操作</th></tr></thead>
          <tbody id="client-rows">${i.clients.map(vt).join("")}</tbody>
        </table>
      </div>
      <div id="client-empty" class="empty-state hidden">没有符合条件的用户</div>
      <footer class="table-footer"><span>共 ${i.clients.length} 个用户</span><span>${((a=(t=i.onlines)==null?void 0:t.user)==null?void 0:a.length)||0} 个在线</span></footer>
    </section>`:""}function vt(e){var r,c,m;const t=!!((c=(r=i==null?void 0:i.onlines)==null?void 0:r.user)!=null&&c.includes(e.name)),a=e.up+e.down,n=R(a,e.volume),s=!!(e.expiry&&e.expiry<Date.now()/1e3),o=`${e.name} ${e.desc} ${e.group}`.toLowerCase();return`<tr data-client-row data-search="${d(o)}" data-group="${d(e.group)}" data-enabled="${e.enable}" data-online="${t}" data-expired="${s}">
    <td><div class="user-cell"><span class="avatar">${d(e.name.slice(0,2).toUpperCase())}</span><div><strong>${d(e.name)}</strong><small>${d(e.desc||e.group||"-")}</small></div></div></td>
    <td><button class="status-toggle ${e.enable?"enabled":""}" data-toggle-client="${e.id}" title="${e.enable?"停用用户":"启用用户"}"><span></span></button><span class="state-label"><span class="status-dot ${t?"online":""}"></span>${t?"在线":e.enable?"离线":"停用"}</span></td>
    <td><div class="usage-cell"><span>${$(a)} / ${e.volume?$(e.volume):"不限"}</span>${e.volume?`<div class="meter small"><span style="width:${n.toFixed(1)}%"></span></div>`:""}</div></td>
    <td><span class="${s?"danger-text":""}">${_(e.expiry)}</span></td>
    <td><span class="count-badge">${((m=e.inbounds)==null?void 0:m.length)||0}</span></td>
    <td><div class="row-actions"><button class="icon-btn" data-copy-sub="${e.id}" title="订阅链接"><i data-lucide="copy"></i></button><button class="icon-btn" data-edit-client="${e.id}" title="编辑用户"><i data-lucide="pencil"></i></button><button class="icon-btn danger" data-delete-client="${e.id}" title="删除用户"><i data-lucide="trash-2"></i></button></div></td>
  </tr>`}function ft(){if(!i)return"";const e=i.inbounds.filter(a=>["vless","hysteria2"].includes(a.type)),t=i.inbounds.filter(a=>!["vless","hysteria2"].includes(a.type));return`
    <section class="protocol-summary">
      ${k("shield-check","加密协议",`${e.length}`,"Reality · Hysteria2")}
      ${k("route","转发入口",`${t.length}`,"直连 SOCKS5")}
      ${k("users","已分配",`${new Set(i.inbounds.flatMap(a=>a.users||[])).size}`,"去重后的入口用户")}
    </section>
    <section class="panel protocol-panel">
      <div class="section-head"><div><span class="eyebrow">Inbound services</span><h2>监听状态</h2></div><a href="/app/inbounds" class="text-btn">高级编辑<i data-lucide="external-link"></i></a></div>
      <div class="protocol-list">${i.inbounds.map(bt).join("")}</div>
    </section>`}function bt(e){var a,n,s;const t=!!((n=(a=i==null?void 0:i.onlines)==null?void 0:a.inbound)!=null&&n.includes(e.tag));return`<div class="protocol-row"><span class="protocol-glyph ${e.type}">${F(e.type,e.tag).slice(0,2).toUpperCase()}</span><div class="protocol-main"><strong>${d(F(e.type,e.tag))}</strong><small>${d(e.tag)}</small></div><span class="protocol-kind">${ct(e.tag)}</span><code>${d(e.listen)}:${e.listen_port}</code><span class="protocol-users"><i data-lucide="users"></i>${((s=e.users)==null?void 0:s.length)||0}</span><span class="status-pill ${t?"ok":"neutral"}">${t?"有连接":"监听中"}</span></div>`}function gt(){var t,a,n,s;const e=u.sys;return`
    <section class="operation-grid">
      <article class="panel operation-main">
        <div class="section-head"><div><span class="eyebrow">Runtime</span><h2>服务控制</h2></div><span class="status-pill ${(t=u.sbd)!=null&&t.running?"ok":"error"}">${(a=u.sbd)!=null&&a.running?"Core online":"Core offline"}</span></div>
        <div class="server-identity"><span class="metric-icon"><i data-lucide="server"></i></span><div><strong>${d((e==null?void 0:e.hostName)||"AaITR")}</strong><small>${d((e==null?void 0:e.cpuType)||"Unknown CPU")}</small></div></div>
        <dl class="detail-list"><div><dt>版本</dt><dd>s-ui ${d((e==null?void 0:e.appVersion)||"-")}</dd></div><div><dt>系统启动</dt><dd>${_(e==null?void 0:e.bootTime,!0)}</dd></div><div><dt>核心运行</dt><dd>${pe((s=(n=u.sbd)==null?void 0:n.stats)==null?void 0:s.Uptime)}</dd></div><div><dt>应用内存</dt><dd>${$(e==null?void 0:e.appMem)}</dd></div></dl>
        <div class="operation-actions"><button class="secondary-btn" id="restart-core"><i data-lucide="rotate-cw"></i>重启核心</button><a class="secondary-btn" href="/app/"><i data-lucide="external-link"></i>高级配置</a></div>
      </article>
      <article class="panel download-panel">
        <div class="section-head"><div><span class="eyebrow">Export</span><h2>备份与导出</h2></div></div>
        <a class="download-row" href="/app/api/getdb"><span><i data-lucide="database-backup"></i></span><div><strong>数据库备份</strong><small>SQLite 完整备份</small></div><i data-lucide="download"></i></a>
        <a class="download-row" href="/app/api/singbox-config"><span><i data-lucide="file-json"></i></span><div><strong>sing-box 配置</strong><small>当前运行配置</small></div><i data-lucide="download"></i></a>
      </article>
      <article class="panel logs-panel">
        <div class="section-head"><div><span class="eyebrow">Logs</span><h2>最近日志</h2></div><button class="icon-btn" id="reload-logs" title="刷新日志"><i data-lucide="refresh-cw"></i></button></div>
        <pre id="runtime-logs"><span class="log-placeholder">点击刷新读取日志</span></pre>
      </article>
    </section>`}function yt(){var e,t,a,n;document.querySelectorAll("[data-route]").forEach(s=>s.addEventListener("click",()=>{M=s.dataset.route})),(e=document.querySelector("[data-go]"))==null||e.addEventListener("click",s=>{const o=s.currentTarget.dataset.go;window.location.hash=`/${o}`}),(t=document.querySelector("#refresh-button"))==null||t.addEventListener("click",()=>C(!0)),(a=document.querySelector("#theme-button"))==null||a.addEventListener("click",()=>{B(document.documentElement.dataset.theme==="dark"?"light":"dark"),z()}),(n=document.querySelector("#logout-button"))==null||n.addEventListener("click",async()=>{try{await y.logout()}catch{}K(),L=!1,i=null,N()}),M==="clients"&&wt(),M==="operations"&&Mt()}function wt(){var e;(e=document.querySelector("#add-client"))==null||e.addEventListener("click",()=>le()),document.querySelectorAll("[data-edit-client]").forEach(t=>t.addEventListener("click",()=>le(Number(t.dataset.editClient)))),document.querySelectorAll("[data-toggle-client]").forEach(t=>t.addEventListener("click",()=>Et(Number(t.dataset.toggleClient)))),document.querySelectorAll("[data-delete-client]").forEach(t=>t.addEventListener("click",()=>kt(Number(t.dataset.deleteClient)))),document.querySelectorAll("[data-copy-sub]").forEach(t=>t.addEventListener("click",()=>Lt(Number(t.dataset.copySub)))),["client-search","client-group-filter","client-state-filter"].forEach(t=>{var a;(a=document.querySelector(`#${t}`))==null||a.addEventListener(t==="client-search"?"input":"change",$t)})}function $t(){var s,o,r,c;const e=((s=document.querySelector("#client-search"))==null?void 0:s.value.toLowerCase().trim())||"",t=((o=document.querySelector("#client-group-filter"))==null?void 0:o.value)||"",a=((r=document.querySelector("#client-state-filter"))==null?void 0:r.value)||"";let n=0;document.querySelectorAll("[data-client-row]").forEach(m=>{var f;const h=!a||a==="online"&&m.dataset.online==="true"||a==="enabled"&&m.dataset.enabled==="true"||a==="disabled"&&m.dataset.enabled==="false"||a==="expired"&&m.dataset.expired==="true",v=(!e||((f=m.dataset.search)==null?void 0:f.includes(e)))&&(!t||m.dataset.group===t)&&h;m.classList.toggle("hidden",!v),v&&(n+=1)}),(c=document.querySelector("#client-empty"))==null||c.classList.toggle("hidden",n!==0)}function Mt(){var e,t;(e=document.querySelector("#restart-core"))==null||e.addEventListener("click",Tt),(t=document.querySelector("#reload-logs"))==null||t.addEventListener("click",ce),ce()}function xt(e=16){const t="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789",a=crypto.getRandomValues(new Uint8Array(e));return Array.from(a,n=>t[n%t.length]).join("")}function St(e){const t=xt(),a=crypto.randomUUID();return{vless:{name:e,uuid:a,flow:"xtls-rprx-vision"},hysteria2:{name:e,password:t}}}function Ct(e,t){return Object.values(e).forEach(a=>{"name"in a&&(a.name=t),"username"in a&&(a.username=t)}),e}async function le(e){if(!i)return;const t=new Set(["vless","hysteria2"]);let a={enable:!0,name:"",config:{},inbounds:i.inbounds.filter(o=>t.has(o.type)).map(o=>o.id),links:[],volume:0,expiry:0,up:0,down:0,desc:"",group:"aaitr-production",remark:"",delayStart:!1,autoReset:!1,resetDays:0,nextReset:0,totalUp:0,totalDown:0};if(e)try{a=await y.loadClient(e)}catch(o){b(o instanceof Error?o.message:"读取用户失败","danger");return}const n=a.expiry?new Date((a.expiry-new Date().getTimezoneOffset()*60)*1e3).toISOString().slice(0,16):"";U(`
    <form id="client-form" class="modal-card wide">
      <header class="modal-head"><div><span class="eyebrow">${e?"Edit client":"New client"}</span><h2>${e?"编辑用户":"新建用户"}</h2></div><button type="button" class="icon-btn" data-close-modal title="关闭"><i data-lucide="x"></i></button></header>
      <div class="modal-body">
        <div class="form-grid">
          <label class="field"><span>名称</span><input name="name" value="${d(a.name)}" required pattern="[A-Za-z0-9._-]+" /></label>
          <label class="field"><span>分组</span><input name="group" value="${d(a.group)}" list="client-groups" required /><datalist id="client-groups">${[...new Set(i.clients.map(o=>o.group))].map(o=>`<option value="${d(o)}"></option>`).join("")}</datalist></label>
          <label class="field"><span>说明</span><input name="desc" value="${d(a.desc)}" /></label>
          <label class="field"><span>备注</span><input name="remark" value="${d(a.remark||"")}" /></label>
          <label class="field"><span>流量上限 (GiB)</span><input name="volume" type="number" min="0" step="1" value="${a.volume?Math.round(a.volume/1024**3):0}" /></label>
          <label class="field"><span>到期时间</span><input name="expiry" type="datetime-local" value="${n}" /></label>
        </div>
        <div class="toggle-row"><label class="check-line"><input name="enable" type="checkbox" ${a.enable?"checked":""} /><span>启用用户</span></label><label class="check-line"><input name="autoReset" type="checkbox" ${a.autoReset?"checked":""} /><span>周期重置</span></label><label class="field compact-field"><span>重置天数</span><input name="resetDays" type="number" min="1" value="${a.resetDays||30}" /></label></div>
        <fieldset class="inbound-fieldset"><legend>可用入口</legend><div class="inbound-options">${i.inbounds.map(o=>`<label class="inbound-option"><input type="checkbox" name="inbounds" value="${o.id}" ${a.inbounds.includes(o.id)?"checked":""} /><span><strong>${d(F(o.type,o.tag))}</strong><small>${d(o.tag)}</small></span></label>`).join("")}</div></fieldset>
        ${e?'<div class="edit-note"><i data-lucide="key-round"></i><span>协议凭据保持不变。修改名称时会同步更新各协议身份。</span></div>':""}
      </div>
      <footer class="modal-actions"><button type="button" class="secondary-btn" data-close-modal>取消</button><button type="submit" class="primary-btn"><i data-lucide="check"></i>保存</button></footer>
    </form>`);const s=document.querySelector("#client-form");s==null||s.addEventListener("submit",async o=>{o.preventDefault();const r=new FormData(s),c=String(r.get("name")||"").trim();if(i==null?void 0:i.clients.some(g=>g.name===c&&g.id!==a.id)){b("用户名称已存在","danger");return}const h=String(r.get("expiry")||""),v=e?Ct(a.config||{},c):St(c),f={...a,enable:r.has("enable"),name:c,config:v,inbounds:r.getAll("inbounds").map(Number),volume:Math.max(0,Number(r.get("volume")||0))*1024**3,expiry:h?Math.floor(new Date(h).getTime()/1e3):0,desc:String(r.get("desc")||"").trim(),group:String(r.get("group")||"").trim(),remark:String(r.get("remark")||"").trim(),autoReset:r.has("autoReset"),resetDays:r.has("autoReset")?Math.max(1,Number(r.get("resetDays")||30)):0,links:a.links||[]},p=s.querySelector('button[type="submit"]');p==null||p.setAttribute("disabled","true");try{await y.saveClient(e?"edit":"new",f),A(),await C(),b(e?"用户已更新":"用户已创建")}catch(g){p==null||p.removeAttribute("disabled"),b(g instanceof Error?g.message:"保存失败","danger")}})}async function Et(e){try{const t=await y.loadClient(e);t.enable=!t.enable,await y.saveClient("edit",t),await C(),b(t.enable?"用户已启用":"用户已停用")}catch(t){b(t instanceof Error?t.message:"操作失败","danger")}}function kt(e){var a;const t=i==null?void 0:i.clients.find(n=>n.id===e);t&&(U(`<section class="modal-card confirm-card"><header class="modal-head"><div><span class="eyebrow">Delete client</span><h2>删除 ${d(t.name)}？</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body"><p>用户凭据和订阅将立即失效，CStoneCloud 出口会在下一次同步中移除该用户。</p></div><footer class="modal-actions"><button class="secondary-btn" data-close-modal>取消</button><button class="danger-btn" id="delete-confirm"><i data-lucide="trash-2"></i>确认删除</button></footer></section>`),(a=document.querySelector("#delete-confirm"))==null||a.addEventListener("click",async()=>{try{await y.saveClient("del",e),A(),await C(),b("用户已删除")}catch(n){b(n instanceof Error?n.message:"删除失败","danger")}}))}function At(e){const t=`${(i==null?void 0:i.subURI)||""}${e}`,a=n=>t.includes("/sub/")?t.replace("/sub/",`/${n}/`):`${t}?format=${n==="clash"?"clash":"json"}`;return[{label:"Clash / Mihomo",value:a("clash")},{label:"sing-box JSON",value:a("json")},{label:"通用订阅",value:t}]}async function Lt(e){const t=i==null?void 0:i.clients.find(n=>n.id===e);if(!t)return;const a=At(t.name);U(`<section class="modal-card subscription-card"><header class="modal-head"><div><span class="eyebrow">Subscription</span><h2>${d(t.name)}</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body subscription-layout"><div class="qr-shell"><canvas id="subscription-qr"></canvas><small>Clash / Mihomo</small></div><div class="subscription-list">${a.map((n,s)=>`<div class="subscription-row"><div><strong>${n.label}</strong><code>${d(n.value)}</code></div><button class="icon-btn" data-copy-value="${s}" title="复制"><i data-lucide="copy"></i></button></div>`).join("")}</div></div></section>`),document.querySelectorAll("[data-copy-value]").forEach(n=>n.addEventListener("click",async()=>{await navigator.clipboard.writeText(a[Number(n.dataset.copyValue)].value),b("订阅链接已复制")}));try{const n=await be(()=>import("./browser-CqDbEFy1.js").then(o=>o.b),[]),s=document.querySelector("#subscription-qr");s&&await n.toCanvas(s,a[0].value,{width:190,margin:1,color:{dark:"#17221d",light:"#ffffff"}})}catch{}}function U(e){A();const t=document.createElement("div");t.id="modal-overlay",t.className="modal-overlay",t.innerHTML=e,document.body.appendChild(t),t.addEventListener("mousedown",a=>{a.target===t&&A()}),t.querySelectorAll("[data-close-modal]").forEach(a=>a.addEventListener("click",A)),document.addEventListener("keydown",he),q()}function he(e){e.key==="Escape"&&A()}function A(){var e;(e=document.querySelector("#modal-overlay"))==null||e.remove(),document.removeEventListener("keydown",he)}async function Tt(){var e;U('<section class="modal-card confirm-card"><header class="modal-head"><div><span class="eyebrow">Restart core</span><h2>重启 sing-box？</h2></div><button class="icon-btn" data-close-modal><i data-lucide="x"></i></button></header><div class="modal-body"><p>现有连接会短暂中断，通常会在数秒内恢复。</p></div><footer class="modal-actions"><button class="secondary-btn" data-close-modal>取消</button><button class="primary-btn" id="restart-confirm"><i data-lucide="rotate-cw"></i>确认重启</button></footer></section>'),(e=document.querySelector("#restart-confirm"))==null||e.addEventListener("click",async()=>{try{await y.restartCore(),A(),b("核心重启指令已发送"),window.setTimeout(()=>C(),3500)}catch(t){b(t instanceof Error?t.message:"重启失败","danger")}})}async function ce(){const e=document.querySelector("#runtime-logs");if(e){e.textContent="正在读取日志...";try{e.textContent=(await y.logs()).join(`
`)||"暂无日志"}catch(t){e.textContent=t instanceof Error?t.message:"读取日志失败"}}}async function C(e=!1){try{const[t,a]=await Promise.all([y.load(),y.status()]);i=t,u=a,L=!0,V=!1,z(),e&&b("数据已刷新")}catch(t){if(V=!1,t instanceof D){L=!1,K(),N();return}i?b(t instanceof Error?t.message:"刷新失败","danger"):N(t instanceof Error?t.message:"无法连接管理服务")}}function me(){K(),P=window.setInterval(()=>{L&&!document.hidden&&C()},15e3)}function K(){P&&window.clearInterval(P),P=void 0}window.addEventListener("hashchange",()=>{M=ue(),L&&z()});lt();V&&dt();C().then(()=>{L&&me()});
