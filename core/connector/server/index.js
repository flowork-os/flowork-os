// @bun
var L=(t,n)=>()=>(n||t((n={exports:{}}).exports,n),n.exports);import { createRequire as __cr } from "module"; var g = __cr(import.meta.url);var U=L((Kt,En)=>{var k=g("path"),H=g("fs"),lt=g("os");class yn{constructor(){this._initialized=!1,this.baseDir=this.resolveBaseDir(),this.configDir=k.join(this.baseDir,"config"),this.dataDir=k.join(this.baseDir,"data"),this.logsDir=k.join(this.baseDir,"logs")}resolveBaseDir(){if(process.env.FLOWORK_CONNECTOR_DIR&&process.env.FLOWORK_CONNECTOR_DIR.trim())return k.resolve(process.env.FLOWORK_CONNECTOR_DIR.trim());if(process.env.FLOWORK_PORTABLE_ROOT&&process.env.FLOWORK_PORTABLE_ROOT.trim())return k.resolve(process.env.FLOWORK_PORTABLE_ROOT.trim(),"connector");if(process.env.FLOWORK_APP_DIR&&H.existsSync(process.env.FLOWORK_APP_DIR)){let n=k.join(process.env.FLOWORK_APP_DIR,"data");try{return H.accessSync(process.env.FLOWORK_APP_DIR,H.constants.W_OK),k.join(process.env.FLOWORK_APP_DIR,"connector")}catch(l){}}let t=lt.homedir()||process.env.HOME||"/tmp";return k.join(t,".flowork","connector")}ensureStructure(){if(this._initialized)return;try{H.mkdirSync(this.configDir,{recursive:!0}),H.mkdirSync(this.dataDir,{recursive:!0}),H.mkdirSync(this.logsDir,{recursive:!0}),this._initialized=!0}catch(t){console.warn(`[Paths] \u26A0\uFE0F Warning initializing directory structure: ${t.message}`)}}getConfigFile(t){return this.ensureStructure(),k.join(this.configDir,t)}getDataFile(t){return this.ensureStructure(),k.join(this.dataDir,t)}getLogFile(t){return this.ensureStructure(),k.join(this.logsDir,t)}}var wn=new yn;wn.ensureStructure();En.exports=wn});var R=L((Ut,kn)=>{var A=g("fs"),W=U();class Cn{constructor(){this.cache=new Map,this.mtimes=new Map,this.initDefaults()}initDefaults(){let t=W.getConfigFile("models.json");if(!A.existsSync(t)){let e={default_model:"gemini-3.8-flash-high",catalog:[{id:"gemini-3.8-flash-high",name:"Gemini 3.8 Flash (High)",owned_by:"flowork"}]};try{A.writeFileSync(t,JSON.stringify(e,null,2))}catch(o){}}let n=W.getConfigFile("network.json");if(!A.existsSync(n)){let e={upstream_host:"https://daily-cloudcode-pa.googleapis.com",user_agent:"antigravity/2.8.1",default_headers:{Accept:"text/event-stream","Content-Type":"application/json",Connection:"close"},timeout_ms:90000,max_retry_attempts:6};try{A.writeFileSync(n,JSON.stringify(e,null,2))}catch(o){}}let l=W.getConfigFile("providers.json");if(!A.existsSync(l)){let e={connector:{id:"connector",name:"Sovereign Connector",badge:"GOOGLE PRO POOL",type:"google_multi_account",desc:"Multi-Account Google Pro Rotator with automatic 429 quota failover."},ollama:{id:"ollama",name:"Ollama Local Engine",badge:"LOCAL GPU",type:"ollama",host:"http://127.0.0.1:11434",default_model:"deepseek-v4-9b-uncensored:latest",custom_models:["deepseek-v4-9b-uncensored:latest","qwen2.5-coder:7b","qwen2.5-coder:1.5b"],desc:"Direct offline inference via your local GPU without internet dependence."},"9router":{id:"9router",name:"9Router Universal Gateway",badge:"ROUTED PROXY",type:"openai_proxy",host:"http://127.0.0.1:20128",api_key:"",default_model:"clinepass/cline-pass/glm-5.2",custom_models:["clinepass/cline-pass/glm-5.2","deepseek/deepseek-r1","openai/gpt-4o","anthropic/claude-3.5-sonnet"],desc:"Universal proxy gateway routing requests to 9Router or OpenAI-compatible backends."}};try{A.writeFileSync(l,JSON.stringify(e,null,2))}catch(o){}}let a=W.getConfigFile("settings.json");if(!A.existsSync(a)){let e={port:9099,host:"127.0.0.1",max_accounts:50,default_rotation_mode:"failover",cooldown_duration_sec:60,token_refresh_margin_sec:300};try{A.writeFileSync(a,JSON.stringify(e,null,2))}catch(o){}}}readJsonCached(t,n={}){let l=W.getConfigFile(t);try{if(!A.existsSync(l))return n;let a=A.statSync(l),e=this.mtimes.get(l)||0;if(this.cache.has(l)&&e===a.mtimeMs)return this.cache.get(l);let o=A.readFileSync(l,"utf8"),r=JSON.parse(o);return this.cache.set(l,r),this.mtimes.set(l,a.mtimeMs),r}catch(a){return console.warn(`[ConfigManager] \u26A0\uFE0F Error reading ${t}: ${a.message}`),this.cache.get(l)||n}}getModels(){return this.readJsonCached("models.json",{default_model:"gemini-3.8-flash-high",catalog:[]})}getNetwork(){return this.readJsonCached("network.json",{upstream_host:"https://daily-cloudcode-pa.googleapis.com",user_agent:"antigravity/2.8.1",default_headers:{Accept:"text/event-stream","Content-Type":"application/json"},timeout_ms:90000,max_retry_attempts:6})}getProviders(){return this.readJsonCached("providers.json",{})}getSettings(){return this.readJsonCached("settings.json",{port:9099,host:"127.0.0.1",max_accounts:50,default_rotation_mode:"failover"})}}kn.exports=new Cn});var cn=L((Vt,Tn)=>{var G=g("fs"),st=g("path"),Y=g("https"),j=g("crypto"),{spawn:V}=g("child_process"),rt=U(),dt=R(),X=rt.getDataFile("vault.json"),z=dt.getSettings(),An=new Map,q=new Map;function ct(t){if(!t||typeof t!=="string")return!1;try{let n=new URL(t.trim());if(n.protocol!=="http:"&&n.protocol!=="https:")return!1;let l=n.href,a=process.env.DISPLAY||":0",e={...process.env,DISPLAY:a};{let o=V("xdg-open",[l],{detached:!0,stdio:"ignore",env:e});o.on("error",()=>{let r=V("google-chrome-stable",[l],{detached:!0,stdio:"ignore",env:e});r.on("error",()=>{V("gio",["open",l],{detached:!0,stdio:"ignore",env:e}).unref()}),r.unref()}),o.unref(),setTimeout(()=>{V("wmctrl",["-xa","google-chrome"],{detached:!0,stdio:"ignore",env:e}).unref()},300)}return!0}catch(n){return console.warn("[Rotator] Failed to launch browser:",n.message),!1}}function T(){try{if(G.existsSync(X)){let n=G.readFileSync(X,"utf8"),l=JSON.parse(n);if(!Array.isArray(l.accounts))l.accounts=[];if(!l.rotation_mode)l.rotation_mode=z.default_rotation_mode;if(!l.session_tickets)l.session_tickets={};if(l.active_provider==="google"||!l.active_provider)l.active_provider="connector";return l}}catch(n){console.warn("[Rotator] Error loading vault file:",n.message)}let t={active_provider:"connector",active_account_id:"",rotation_mode:z.default_rotation_mode,flowork_token:"",flowork_user:null,is_logged_out:!1,accounts:[],session_tickets:{},pending_oauth_sessions:{}};return S(t),t}function S(t){try{let n=st.dirname(X);if(!G.existsSync(n))G.mkdirSync(n,{recursive:!0});let l=`${X}.tmp.${Date.now()}`;G.writeFileSync(l,JSON.stringify(t,null,2),"utf8"),G.renameSync(l,X)}catch(n){console.error("[Rotator] Error writing vault file:",n.message)}}function pt(t=9099){let n="flw_tkt_"+Date.now().toString(36)+"_"+j.randomBytes(8).toString("hex"),l={port:t,created_at:Date.now(),expires_at:Date.now()+1800000};q.set(n,l);let a=T();if(!a.session_tickets)a.session_tickets={};a.session_tickets[n]=l,a.last_ticket=n,S(a);let e=`https://auth.floworkos.com/?ticket=${n}&port=${t}`;return{ticket:n,gateUrl:e}}function bt(t){if(!t)return null;if(q.has(t)){let l=q.get(t);return q.delete(t),l}let n=T();if(n.session_tickets&&n.session_tickets[t]){let l=n.session_tickets[t];return delete n.session_tickets[t],S(n),l}return null}async function ft(t){if(!t)return{valid:!1,error:"Token missing"};return new Promise((n)=>{let l=Y.request("https://auth.floworkos.com/api/auth/verify",{method:"GET",headers:{Authorization:`Bearer ${t}`,"User-Agent":"MrFlow-Connector/1.0"},timeout:6000},(a)=>{let e="";a.on("data",(o)=>e+=o),a.on("end",()=>{try{let o=JSON.parse(e);if(o.valid&&o.user)return n({valid:!0,user:o.user});n({valid:!1,error:o.error||"Token invalid"})}catch(o){n({valid:!1,error:o.message})}})});l.on("timeout",()=>{l.destroy(Error("TIMEOUT")),n({valid:!1,error:"Verification timed out"})}),l.on("error",(a)=>n({valid:!1,error:a.message})),l.end()})}async function ut(t=null){let n=T(),l=t||n.flowork_token;if(!l)return{success:!1,error:"No active session token from auth.floworkos.com"};return new Promise((a)=>{let e=Y.request("https://auth.floworkos.com/api/connector/vault",{method:"GET",headers:{Authorization:`Bearer ${l}`,"User-Agent":"MrFlow-Connector/1.0"},timeout:8000},(o)=>{let r="";o.on("data",(i)=>r+=i),o.on("end",()=>{try{let i=JSON.parse(r);if(i&&i.success&&i.exists&&i.vault){let c=(Array.isArray(i.vault.accounts)?i.vault.accounts:[]).filter((s)=>s&&s.email&&(s.access_token||s.refresh_token)).map((s)=>({id:s.id||"acc_"+Date.now().toString(36)+"_"+Math.random().toString(36).substring(2,6),email:s.email,name:s.name||s.email.split("@")[0],access_token:s.access_token||"",refresh_token:s.refresh_token||"",expires_at:s.expires_at||0,client_id:s.client_id||"",status:s.status||"ready",cooldown_until:0,requests_count:s.requests_count||0,errors_count:s.errors_count||0,added_at:s.added_at||new Date().toISOString(),last_used_at:s.last_used_at||new Date().toISOString()}));if(n.accounts=c,c.length>0)n.active_account_id=i.vault.active_account_id||c[0].id;return n.rotation_mode=i.vault.rotation_mode||n.rotation_mode||"failover",S(n),console.log(`[Rotator] \u2601\uFE0F Successfully synchronized ${c.length} accounts from auth.floworkos.com Cloud Vault!`),a({success:!0,count:c.length,accounts:c,active_account_id:n.active_account_id})}if(i&&i.success&&!i.exists)return a({success:!0,count:0,accounts:[],message:"Cloud vault exists but has no accounts stored yet."});a({success:!1,error:i.error||"Failed to parse cloud vault"})}catch(i){a({success:!1,error:"Invalid response from cloud vault: "+i.message})}})});e.on("timeout",()=>{e.destroy(Error("TIMEOUT")),a({success:!1,error:"Cloud vault request timed out"})}),e.on("error",(o)=>a({success:!1,error:o.message})),e.end()})}async function gt(t=null){let n=t||T(),l=n.flowork_token;if(!l)return{success:!1,error:"Not authenticated"};let a=n.accounts.map((r)=>({id:r.id,email:r.email,name:r.name,access_token:r.access_token||"",refresh_token:r.refresh_token||"",expires_at:r.expires_at||0,status:r.status||"ready",added_at:r.added_at,last_used_at:r.last_used_at})),e={active_provider:"google",rotation_mode:n.rotation_mode||"failover",active_account_id:n.active_account_id||"",accounts:a,last_updated:new Date().toISOString()},o=JSON.stringify({vault:e});return new Promise((r)=>{let i=Y.request("https://auth.floworkos.com/api/connector/vault",{method:"POST",headers:{Authorization:`Bearer ${l}`,"Content-Type":"application/json","Content-Length":Buffer.byteLength(o),"User-Agent":"MrFlow-Connector/1.0"},timeout:8000},(d)=>{let c="";d.on("data",(s)=>c+=s),d.on("end",()=>{try{let s=JSON.parse(c);r({success:!!s.success,data:s})}catch(s){r({success:!1,error:s.message})}})});i.on("error",(d)=>r({success:!1,error:d.message})),i.write(o),i.end()})}function mt(t){try{let n=t.split(".");if(n.length<2)return null;let l=Buffer.from(n[1],"base64").toString("utf8");return JSON.parse(l)}catch(n){return null}}async function xt(t){return new Promise((n)=>{let l=Y.request("https://www.googleapis.com/oauth2/v3/userinfo",{method:"GET",headers:{Authorization:`Bearer ${t}`,"User-Agent":"MrFlowConnector/1.0"},timeout:8000},(a)=>{let e="";a.on("data",(o)=>e+=o),a.on("end",()=>{try{let o=JSON.parse(e);n({success:!0,user:o})}catch(o){n({success:!1,error:o.message})}})});l.on("error",(a)=>n({success:!1,error:a.message})),l.end()})}async function ht(t){let n=j.randomBytes(32).toString("base64url"),l=j.createHash("sha256").update(n).digest("base64url"),a="flw_multi_"+t+"_"+Date.now().toString(36)+"_"+j.randomBytes(6).toString("hex"),e="http://localhost:51121/oauth-callback";An.set(a,{verifier:n,redirectUri:"http://localhost:51121/oauth-callback",createdAt:Date.now()});let o=T();if(!o.pending_oauth_sessions)o.pending_oauth_sessions={};o.pending_oauth_sessions[a]={verifier:n,redirectUri:"http://localhost:51121/oauth-callback",provider:"antigravity",createdAt:Date.now()},S(o);try{let d=await(await fetch("https://auth.floworkos.com/api/auth/oauth/init",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({provider:"antigravity",state:a,codeChallenge:l,redirectUri:"http://localhost:51121/oauth-callback"})})).json();if(d&&d.authUrl)return{loginUrl:d.authUrl,state:a,redirectUri:"http://localhost:51121/oauth-callback"}}catch(i){console.warn("[Rotator] auth.floworkos.com init error:",i.message)}return{loginUrl:`https://auth.floworkos.com/api/auth/oauth/init?provider=antigravity&state=${encodeURIComponent(a)}&redirectUri=${encodeURIComponent("http://localhost:51121/oauth-callback")}&codeChallenge=${encodeURIComponent(l)}`,state:a,redirectUri:"http://localhost:51121/oauth-callback"}}async function vt(t,n,l){return new Promise((a)=>{let e=JSON.stringify({code:t,verifier:n||"",code_verifier:n||"",provider:"antigravity",redirectUri:l||"http://localhost:51121/oauth-callback"}),o=T(),r={"Content-Type":"application/json","User-Agent":"MrFlow-Connector/1.0","Content-Length":Buffer.byteLength(e)};if(o.flowork_token)r.Authorization=`Bearer ${o.flowork_token}`;let i=Y.request("https://auth.floworkos.com/api/auth/oauth/exchange",{method:"POST",headers:r,timeout:15000},(d)=>{let c="";d.on("data",(s)=>c+=s),d.on("end",()=>{try{let s=JSON.parse(c);if(s.success&&(s.accessToken||s.access_token))return a({success:!0,tokens:{access_token:s.accessToken||s.access_token,refresh_token:s.refreshToken||s.refresh_token,expires_in:s.expiresIn||3600,id_token:s.idToken||s.id_token,email:s.email||s.user?.email||s.user_email}});a({success:!1,error:s.error||"Token exchange failed"})}catch(s){a({success:!1,error:s.message})}})});i.on("error",(d)=>a({success:!1,error:d.message})),i.write(e),i.end()})}async function dn(t,n=!1){if(!t||!t.refresh_token)return{refreshed:!1,reason:"NO_REFRESH_TOKEN"};let l=Date.now();if(!n&&t.expires_at&&t.expires_at-l>(z.token_refresh_margin_sec||300)*1000)return{refreshed:!1,reason:"TOKEN_STILL_VALID",access_token:t.access_token};return new Promise((a)=>{let e=T(),o=JSON.stringify({refreshToken:t.refresh_token,provider:"antigravity"}),r={"Content-Type":"application/json","User-Agent":"MrFlow-Connector/1.0","Content-Length":Buffer.byteLength(o)};if(e.flowork_token)r.Authorization=`Bearer ${e.flowork_token}`;let i=Y.request("https://auth.floworkos.com/api/auth/oauth/refresh",{method:"POST",headers:r,timeout:1e4},(d)=>{let c="";d.on("data",(s)=>c+=s),d.on("end",()=>{try{let s=JSON.parse(c);if(s.success&&(s.accessToken||s.access_token)){if(t.access_token=s.accessToken||s.access_token,s.refreshToken||s.refresh_token)t.refresh_token=s.refreshToken||s.refresh_token;let p=s.expiresIn||s.expires_in||3600;t.expires_at=Date.now()+p*1000,t.status="active",t.error_message="",console.log(`[Rotator] \u2705 Token refreshed for ${t.email} (valid for ${p}s)`),a({refreshed:!0,access_token:t.access_token})}else t.status="error",t.error_message=s.error||"Refresh failed",console.error(`[Rotator] Refresh failed for ${t.email}:`,s.error),a({refreshed:!1,error:t.error_message})}catch(s){a({refreshed:!1,error:s.message})}})});i.on("timeout",()=>{i.destroy(Error("TIMEOUT")),a({refreshed:!1,error:"Token refresh timed out"})}),i.on("error",(d)=>a({refreshed:!1,error:d.message})),i.write(o),i.end()})}async function yt(t){if(!t)return{valid:!1,error:"No account specified"};let n=Date.now(),l=(z.token_refresh_margin_sec||300)*1000;if(t.access_token&&t.expires_at&&t.expires_at-n>l)return{valid:!0,access_token:t.access_token};let a=await dn(t,!0);return{valid:a.refreshed||!a.error,access_token:t.access_token,details:a}}function Sn(t,n=null){if(!Array.isArray(t.accounts)||t.accounts.length===0)return null;let l=Date.now(),a=t.accounts.find((i)=>i.id===t.active_account_id);if(a&&(!n||a.id!==n)&&(!a.cooldown_until||a.cooldown_until<=l)&&a.status!=="error")return a;let o=t.accounts.find((i)=>{if(n&&i.id===n)return!1;return!(i.cooldown_until&&i.cooldown_until>l)&&i.status!=="error"});if(o)return t.active_account_id=o.id,S(t),o;let r=t.accounts.find((i)=>!n||i.id!==n)||t.accounts[0];if(r)t.active_account_id=r.id,S(t);return r}function wt(t,n=null,l="429_LIMIT"){let a=T(),e=a.accounts.findIndex((d)=>d.id===t);if(e===-1)return null;let o=a.accounts[e],r=n||z.cooldown_duration_sec||60;o.cooldown_until=Date.now()+r*1000,o.status="cooldown",o.errors_count=(o.errors_count||0)+1,o.error_message=l,console.warn(`[Rotator] \uD83D\uDED1 Account [${o.email}] entered cooldown for ${r}s (${l}). Moving to end of queue.`),a.accounts.splice(e,1),a.accounts.push(o);let i=Sn(a,t);if(i)a.active_account_id=i.id,console.log(`[Rotator] \uD83D\uDD00 Switched active account to next in line: [${i.email}]`);return S(a),{account:o,next_active:i}}function Et(){let t=T(),n=0;for(let l of t.accounts)if(l.cooldown_until&&l.cooldown_until>Date.now()||l.status==="cooldown"||l.status==="error")l.cooldown_until=0,l.status="ready",l.error_message="",n++;return S(t),console.log(`[Rotator] \u26A1 Cleared cooldowns and errors for ${n} accounts.`),n}function Ct(t=60000){setInterval(async()=>{try{let n=T();if(!n.flowork_token)return;if(!Array.isArray(n.accounts)||n.accounts.length===0)return;let l=Date.now(),a=(z.token_refresh_margin_sec||300)*1000;for(let e of n.accounts)if(e.refresh_token&&e.expires_at&&e.expires_at-l<=a)console.log(`[Rotator Keeper] Proactively refreshing expiring token for: ${e.email}`),await dn(e,!0),S(n)}catch(n){console.warn("[Rotator Keeper] Background refresh error:",n.message)}},t)}Tn.exports={loadVault:T,saveVault:S,config:z,pendingPkceSessions:An,openUrlInBrowser:ct,parseJwtClaims:mt,fetchGoogleUserInfo:xt,generateLoginUrl:ht,exchangeOAuthCode:vt,refreshAccountToken:dn,ensureAccountTokenValid:yt,getNextAvailableAccount:Sn,markAccountCooldown:wt,clearAllCooldowns:Et,startBackgroundTokenKeeper:Ct,createSessionTicket:pt,resolveSessionTicket:bt,verifyFloworkToken:ft,pullCloudVault:ut,pushCloudVault:gt}});var zn=L((qt,_n)=>{var{Transform:Mn}=g("stream"),In=g("crypto"),jt=R();function Ln(t){return"gemini-3.8-flash-high"}function kt(t,n="gemini-3.8-flash-high"){let l=Array.isArray(t.messages)?t.messages:[],a=Ln(t.model||n),e=[],o=null;for(let i of l){let d=(i.role||"user").toLowerCase(),c=typeof i.content==="string"?i.content:Array.isArray(i.content)?i.content.map((p)=>p.text||"").join(`
`):"";if(d==="system"){if(!o)o={parts:[{text:c}]};else o.parts[0].text+=`

`+c;continue}let s=d==="assistant"?"model":"user";e.push({role:s,parts:[{text:c}]})}if(e.length===0)e.push({role:"user",parts:[{text:""}]});let r={maxOutputTokens:t.max_tokens||t.max_completion_tokens||65536};if(t.temperature!==void 0)r.temperature=t.temperature;if(t.top_p!==void 0)r.topP=t.top_p;return{project:"aicode-consumers",model:a,request:{contents:e,systemInstruction:o,generationConfig:r}}}function At(t,n,isLocal=!1){let l=t.request||t,a=l.contents||[],e=l.systemInstruction,o=[];if(e&&e.parts){if(isLocal){o.push({role:"system",content:"You are Mr. Flow (mrflow), the sovereign autonomous AI agent of Flowork OS. Always respond concisely, accurately, and directly in the user's language."})}else{let r=e.parts.filter((i)=>i.text).map((i)=>i.text).join(`

`).trim();if(r)o.push({role:"system",content:r})}}for(let r of a){let i=r.role==="model"?"assistant":"user",d=r.parts||[],c="";for(let s of d){if(s.text){let txt=s.text;if(isLocal&&txt.includes("<session_context>")){txt=txt.replace(/<session_context>[\s\S]*?<\/session_context>/g,"<session_context>OS: Flowork Linux 7.3.0 Rust. Workspace: /opt/floworkos.</session_context>")}c+=(c?`
`:"")+txt}}if(c)o.push({role:i,content:c})}return{model:n,messages:o,stream:!0}}class $n extends Mn{constructor(t="gemini-3.8-flash-high",n={}){super(n);this.model=t,this.buffer="",this.completionId="chatcmpl-"+In.randomBytes(12).toString("hex"),this.created=Math.floor(Date.now()/1000),this.hasSentStart=!1}_transform(t,n,l){this.buffer+=t.toString("utf8");let a=this.buffer.split(`
`);this.buffer=a.pop()||"";for(let e of a){let o=e.trim();if(!o||o.startsWith(":"))continue;if(o.startsWith("data:")){let r=o.slice(5).trim();if(r==="[DONE]")continue;try{let i=JSON.parse(r),s=((i.response||i).candidates||[])[0];if(s&&s.content&&Array.isArray(s.content.parts)){for(let p of s.content.parts)if(p.text){let b={id:this.completionId,object:"chat.completion.chunk",created:this.created,model:this.model,choices:[{index:0,delta:{content:p.text},finish_reason:null}]};this.push(`data: ${JSON.stringify(b)}

`)}}if(s&&s.finishReason&&s.finishReason!=="STOP");}catch(i){}}}l()}_flush(t){let n={id:this.completionId,object:"chat.completion.chunk",created:this.created,model:this.model,choices:[{index:0,delta:{},finish_reason:"stop"}]};this.push(`data: ${JSON.stringify(n)}

`),this.push(`data: [DONE]

`),t()}}class On extends Mn{constructor(t={}){super(t);this.buffer=""}_transform(t,n,l){this.buffer+=t.toString("utf8");let a=this.buffer.split(`\n`);this.buffer=a.pop()||"";for(let e of a){let o=e.trim();if(!o||o.startsWith(":"))continue;if(o.startsWith("data:")){let r=o.slice(5).trim();if(r==="[DONE]"){this._emitStop();continue}try{let d=JSON.parse(r).choices?.[0]?.delta;if(d){let th=d.reasoning||d.reasoning_content||"";if(th){let c={response:{candidates:[{content:{role:"model",parts:[{thought:!0,text:th}]},finishReason:null}]},candidates:[{content:{role:"model",parts:[{thought:!0,text:th}]},finishReason:null}]};this.push(`data: ${JSON.stringify(c)}\n\n`)}let txt=d.content||"";if(txt){let c={response:{candidates:[{content:{role:"model",parts:[{text:txt}]},finishReason:null}]},candidates:[{content:{role:"model",parts:[{text:txt}]},finishReason:null}]};this.push(`data: ${JSON.stringify(c)}\n\n`)}}}catch(i){}}}l()}_flush(t){this._emitStop(),t()}_emitStop(){let t={response:{candidates:[{content:{role:"model",parts:[]},finishReason:"STOP"}]},candidates:[{content:{role:"model",parts:[]},finishReason:"STOP"}]};this.push(`data: ${JSON.stringify(t)}\n\n`)}}function St(t){let n="",l=t.split(`
`);for(let a of l){let e=a.trim();if(e.startsWith("data:")){let o=e.slice(5).trim();if(o==="[DONE]")continue;try{let r=JSON.parse(o),c=((r.response||r).candidates||[])[0];if(c&&c.content&&Array.isArray(c.content.parts)){for(let s of c.content.parts)if(s.text)n+=s.text}}catch(r){}}}return n}function Tt(t,n="gemini-3.8-flash-high"){return{id:"chatcmpl-"+In.randomBytes(12).toString("hex"),object:"chat.completion",created:Math.floor(Date.now()/1000),model:n,choices:[{index:0,message:{role:"assistant",content:t},finish_reason:"stop"}],usage:{prompt_tokens:0,completion_tokens:0,total_tokens:0}}}_n.exports={normalizeModel:Ln,openAiToGemini:kt,geminiToOpenAi:At,GeminiToOpenAiStream:$n,OpenAiToGeminiStream:On,parseGeminiSseToFullText:St,createOpenAiJsonResponse:Tt}});var Fn=L((ee,Yn)=>{var Mt=g("fs"),ne=g("path"),bn=g("https"),Nn=g("http"),te=g("url"),{Transform:It}=g("stream"),$=cn(),{normalizeModel:pn,openAiToGemini:Lt,geminiToOpenAi:Bn,GeminiToOpenAiStream:$t,OpenAiToGeminiStream:Hn,parseGeminiSseToFullText:Ot,createOpenAiJsonResponse:_t}=zn(),Rn=R();function Pn(){return Rn.getModels().catalog||[]}function zt(){return Rn.getNetwork()}async function Pt(t,n,l,a){console.log(`[Proxy Request] ${t.method} ${a}`);let e=$.loadVault(),o=(e.active_provider||"connector").toLowerCase();if(a==="/v1/models"||a==="/models"){if(o==="ollama"){let d=e.providers?.ollama||{},c=d.custom_models||[d.default_model||"deepseek-v4-9b-uncensored:latest"];return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({object:"list",data:c.map((s)=>({id:s,object:"model",created:1700000000,owned_by:"ollama"}))}))}if(o==="9router"||o==="router9"){let d=e.providers?.["9router"]||{},c=d.custom_models||[d.default_model||"clinepass/cline-pass/glm-5.2"];return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({object:"list",data:c.map((s)=>({id:s,object:"model",created:1700000000,owned_by:"9router"}))}))}let i=Pn();return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({object:"list",data:i.map((d)=>({id:d.id,object:"model",created:1700000000,owned_by:d.owned_by||"flowork"}))}))}if(a==="/v1beta/models"){let i=Pn();return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({models:i.map((d)=>({name:`models/${d.id}`,version:"1.0",displayName:d.name,description:`Sovereign Flowork Model ${d.name}`,inputTokenLimit:1048576,outputTokenLimit:65536,supportedGenerationMethods:["generateContent","streamGenerateContent"]}))}))}if(a.includes(":loadCodeAssist"))return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({allowed:!0,cloudaicompanionProject:"aicode-consumers",currentTier:{id:"enterprise-tier",name:"MrFlow Enterprise Sovereign",description:"Full Autonomous Agent Access",isDefault:!0},allowedTiers:[{id:"enterprise-tier",name:"MrFlow Enterprise Sovereign",description:"Full Autonomous Agent Access",isDefault:!0}],gcpManaged:!1,manageSubscriptionUri:"https://auth.floworkos.com"}));if(a.includes(":retrieveUserQuota")||a.includes("UserQuotaSummary"))return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({dailyQuota:"999999999",remainingQuota:"999999999",resetTime:"2099-01-01T00:00:00Z",allowed:!0}));if(a.includes(":listExperiments"))return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({experimentIds:[],flags:[]}));if(a.includes(":fetchUserInfo")||a.includes("/fetchUserInfo")){let i=e.accounts.find((s)=>s.id===e.active_account_id)||e.accounts[0]||{},d=i.email||(e.flowork_user?.email||"user@floworkos.com"),c=i.name||(e.flowork_user?.name||e.flowork_user?.username||"Flowork Operator");return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({user:{email:d,name:c,tier:e.flowork_user?.tier?`${e.flowork_user.tier}-tier`:"enterprise-tier"}}))}let r=[];t.on("data",(i)=>r.push(i)),t.on("end",async()=>{let i=Buffer.concat(r);if(o==="ollama")return Nt(t,n,a,i,e);if(o==="9router"||o==="router9")return Bt(t,n,a,i,e);return Gt(t,n,a,l.query,i,e)})}async function Nt(t,n,l,a,e){let isStream=l.includes("stream")||l.includes("alt=sse"),isChat=l.includes("/chat/completions");if(!isStream&&!isChat&&(l.includes("generateContent")||l.includes("GenerateContent"))){let gResp={response:{candidates:[{content:{role:"model",parts:[{text:JSON.stringify({complexity_reasoning:"Direct query",complexity_score:1,category:0,status:"ok"})}]},finishReason:"STOP"}],usageMetadata:{promptTokenCount:10,candidatesTokenCount:10,totalTokenCount:20}},candidates:[{content:{role:"model",parts:[{text:JSON.stringify({complexity_reasoning:"Direct query",complexity_score:1,category:0,status:"ok"})}]},finishReason:"STOP"}],usageMetadata:{promptTokenCount:10,candidatesTokenCount:10,totalTokenCount:20}};return n.writeHead(200,{"Content-Type":"application/json; charset=utf-8"}),n.end(JSON.stringify(gResp))}let o=e.providers?.ollama||{},r=(o.host||o.endpoint||"http://127.0.0.1:11434").replace(/\/+$/,""),i=o.default_model||o.model||"deepseek-v4-9b-uncensored:latest",d=isChat,c,parsedReq={};try{parsedReq=JSON.parse(a.toString("utf8")||"{}");if(d){if(!parsedReq.model)parsedReq.model=i;if(!parsedReq.options)parsedReq.options={num_ctx:8192};c=JSON.stringify(parsedReq)}else{let p=Bn(parsedReq,i,!0);if(!isStream)p.stream=!1;if(!p.options)p.options={num_ctx:8192};c=JSON.stringify(p)}}catch(s){c=a}try{let s=new URL("/v1/chat/completions",r),b=(s.protocol==="https:"?bn:Nn).request(s.toString(),{method:"POST",headers:{"Content-Type":"application/json","Content-Length":Buffer.byteLength(c)},timeout:120000},(u)=>{if(u.statusCode!==200)return n.writeHead(u.statusCode,u.headers),u.pipe(n);if(d)return n.writeHead(200,u.headers),u.pipe(n);if(isStream){n.writeHead(200,{"Content-Type":"text/event-stream; charset=utf-8","Cache-Control":"no-cache",Connection:"keep-alive"});let E=new Hn({modelName:i});u.pipe(E).pipe(n)}else{let buf="";u.on("data",(k)=>buf+=k),u.on("end",()=>{try{let rj=JSON.parse(buf||"{}"),msg=rj.choices?.[0]?.message||{},rawTxt=msg.content||"",cleanTxt=rawTxt.replace(/<think>[\s\S]*?<\/think>/gi,"").trim();if(!cleanTxt&&msg.reasoning){let m=msg.reasoning.match(/\{[\s\S]*?\}/);if(m)cleanTxt=m[0]}let isValidJson=false;if(cleanTxt){try{JSON.parse(cleanTxt);isValidJson=true}catch(_){let m=(cleanTxt||msg.reasoning||"").match(/\{[\s\S]*?\}/);if(m){try{JSON.parse(m[0]);cleanTxt=m[0];isValidJson=true}catch(_){}}}}if(!isValidJson&&(parsedReq.generationConfig?.responseMimeType==="application/json"||l.includes("generateContent")))cleanTxt=JSON.stringify({category:0,status:"ok"});let pts=[{text:cleanTxt||rawTxt||"OK"}];let gResp={response:{candidates:[{content:{role:"model",parts:pts},finishReason:"STOP"}],usageMetadata:{promptTokenCount:rj.usage?.prompt_tokens||0,candidatesTokenCount:rj.usage?.completion_tokens||0,totalTokenCount:rj.usage?.total_tokens||0}},candidates:[{content:{role:"model",parts:pts},finishReason:"STOP"}],usageMetadata:{promptTokenCount:rj.usage?.prompt_tokens||0,candidatesTokenCount:rj.usage?.completion_tokens||0,totalTokenCount:rj.usage?.total_tokens||0}};n.writeHead(200,{"Content-Type":"application/json; charset=utf-8"}),n.end(JSON.stringify(gResp))}catch(pe){n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:pe.message,raw:buf}))}})}});b.on("error",(u)=>{n.writeHead(502,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:502,message:`Ollama connection failed at ${r}: ${u.message}. Ensure Ollama is running.`,status:"BAD_GATEWAY"}}))}),b.write(c),b.end()}catch(s){n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:500,message:s.message}}))}}async function Bt(t,n,l,a,e){let o=e.providers?.["9router"]||{},r=(o.host||"http://127.0.0.1:20128").replace(/\/+$/,""),i=o.api_key||"",d=o.default_model||"clinepass/cline-pass/glm-5.2",c=l.includes("/chat/completions"),s;try{let p=JSON.parse(a.toString("utf8")||"{}");if(c){if(!p.model)p.model=d;s=JSON.stringify(p)}else{let b=Bn(p,d);s=JSON.stringify(b)}}catch(p){s=a}try{let p=r.endsWith("/v1")?"/chat/completions":"/v1/chat/completions",b=new URL(p,r),u=b.protocol==="https:"?bn:Nn,E={"Content-Type":"application/json","Content-Length":Buffer.byteLength(s)};if(i)E.Authorization=`Bearer ${i}`;let w=u.request(b.toString(),{method:"POST",headers:E,timeout:90000},(y)=>{if(y.statusCode!==200)return n.writeHead(y.statusCode,y.headers),y.pipe(n);if(c)return n.writeHead(200,y.headers),y.pipe(n);n.writeHead(200,{"Content-Type":"text/event-stream; charset=utf-8","Cache-Control":"no-cache",Connection:"keep-alive"});let m=new Hn({modelName:d});y.pipe(m).pipe(n)});w.on("error",(y)=>{n.writeHead(502,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:502,message:`9Router connection failed at ${r}: ${y.message}.`,status:"BAD_GATEWAY"}}))}),w.write(s),w.end()}catch(p){n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:500,message:p.message}}))}}function nn(t){if(!t||typeof t!=="object")return t;if(Array.isArray(t))return t.map(nn);let n=new Set(["type","format","description","nullable","enum","properties","required","items","minItems","maxItems","minimum","maximum","default"]),l={};for(let[a,e]of Object.entries(t)){if(!n.has(a))continue;if(a==="type"&&typeof e==="string")l.type=e.toUpperCase();else if(a==="properties"&&e&&typeof e==="object"){l.properties={};for(let[o,r]of Object.entries(e))l.properties[o]=nn(r)}else if(a==="items"&&e&&typeof e==="object")l.items=nn(e);else l[a]=e}return l}class Gn extends It{constructor(){super();this.buffer=""}_transform(t,n,l){this.buffer+=t.toString("utf8");let a=this.buffer.split(`
`);this.buffer=a.pop();for(let e of a){let o=e.trim();if(o.startsWith("data:")){let r=o.slice(5).trim();if(r==="[DONE]"){this.push(`data: [DONE]

`);continue}try{let i=JSON.parse(r),d=i.response||i;this.push(`data: ${JSON.stringify(d)}

`)}catch(i){this.push(e+`
`)}}else if(o.length>0)this.push(e+`
`)}l()}_flush(t){if(this.buffer.trim().length>0){let n=this.buffer.trim();if(n.startsWith("data:")){let l=n.slice(5).trim();try{let a=JSON.parse(l),e=a.response||a;this.push(`data: ${JSON.stringify(e)}

`)}catch(a){this.push(this.buffer+`

`)}}else this.push(this.buffer+`

`)}t()}}function Ht(t){if(!Array.isArray(t)||t.length===0)return t;let n=[];for(let l of t){if(!l||!l.role)continue;let a=n[n.length-1];if(a&&a.role===l.role)a.parts=(a.parts||[]).concat(l.parts||[]);else n.push({role:l.role,parts:[...l.parts||[]]})}return n}function Rt(t){if(Array.isArray(t.contents))t.contents=Ht(t.contents)}async function Gt(t,n,l,a,e,o){if(!o.flowork_token)return n.writeHead(401,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:401,message:"Sovereign Router is locked. Please sign in to auth.floworkos.com in the Connector GUI.",status:"UNAUTHENTICATED"}}));if(!Array.isArray(o.accounts)||o.accounts.length===0)return n.writeHead(404,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:404,message:'No Google accounts found in pool. Use "Unduh Akun (Sync Cloud)" in the GUI.',status:"NOT_FOUND"}}));let r=l.includes("/chat/completions"),i=l.match(/\/v1beta\/models\/([^:?]+):([^?]+)/),d=!!i,c=null;try{if(e&&e.length>0)c=JSON.parse(e.toString("utf8")),Mt.writeFileSync("/tmp/gemini_cli_last_req.json",JSON.stringify(c,null,2))}catch(m){}let s=null,p=!0,b="gemini-3.8-flash-high";if(r)p=c?.stream!==!1,b=pn(c?.model||"gemini-3.8-flash-high"),s=Lt(c||{},b);else if(d){p=(i[2]||"").includes("stream"),b=pn(i[1]||"gemini-3.8-flash-high");let x=c?.request||c||{};if(!x.generationConfig)x.generationConfig={};if(!x.generationConfig.maxOutputTokens)x.generationConfig.maxOutputTokens=65536;if(Rt(x),Array.isArray(x.tools))for(let F of x.tools){let N=F.functionDeclarations||F.function_declarations;if(Array.isArray(N)){for(let h of N){for(let I of Object.keys(h))if(I!=="name"&&I!=="description"&&I!=="parameters"&&I!=="response"&&I!=="parametersJsonSchema")delete h[I];let O=h.parametersJsonSchema||h.parameters;if(O)h.parameters=nn(O),delete h.parametersJsonSchema}F.functionDeclarations=N,delete F.function_declarations}}s={project:"aicode-consumers",model:b,request:x}}else{if(p=l.includes("stream")||t.headers.accept?.includes("event-stream"),s=c,s&&!s.project)s.project="aicode-consumers";if(s?.model)b=pn(s.model)}let u=s?Buffer.from(JSON.stringify(s),"utf8"):e,E="/v1internal:streamGenerateContent?alt=sse",w=Math.min(o.accounts.length,6),y=null;for(let m=0;m<w;m++){let x=$.getNextAvailableAccount(o);if(!x)break;if(!(await $.ensureAccountTokenValid(x)).valid){$.markAccountCooldown(x.id,120,"TOKEN_INVALID");continue}x.requests_count=(x.requests_count||0)+1,x.last_used_at=new Date().toISOString(),$.saveVault(o);let N=await new Promise((h)=>{console.log(`[Proxy] \uD83D\uDCE1 Routing ${r?"OpenAI":d?"Gemini":"Native"} request -> Google [${x.email}] (model: ${b})`);let O=zt(),I=O.upstream_host||"https://daily-cloudcode-pa.googleapis.com",gn=new URL(E,I),et={Host:gn.host,Authorization:`Bearer ${x.access_token}`,"User-Agent":O.user_agent||"antigravity/2.8.1",...O.default_headers||{},"Content-Length":u.length},Q=bn.request(gn.toString(),{method:"POST",headers:et,timeout:O.timeout_ms||90000},(v)=>{if(v.statusCode===429)return console.warn(`[Proxy] \u26A0\uFE0F Account [${x.email}] hit 429 Quota Exceeded. Rotating account...`),$.markAccountCooldown(x.id,60,"HTTP_429_QUOTA_EXHAUSTED"),v.resume(),h({retry:!0,reason:"429"});if(v.statusCode===401)return console.warn(`[Proxy] \u26A0\uFE0F Account [${x.email}] returned 401. Refreshing token...`),$.refreshAccountToken(x,!0).catch(()=>{}),$.markAccountCooldown(x.id,30,"TOKEN_REFRESH_REQUIRED"),v.resume(),h({retry:!0,reason:"401"});if(v.statusCode===403){let C="";v.on("data",(D)=>C+=D),v.on("end",()=>{console.warn(`[Proxy] \u26A0\uFE0F Account [${x.email}] returned 403 Forbidden. Rotating...`),$.markAccountCooldown(x.id,86400,"FORBIDDEN_403"),h({retry:!0,reason:"403",message:C})});return}if(v.statusCode!==200){let C="";v.on("data",(D)=>C+=D),v.on("end",()=>{console.warn(`[Proxy] Upstream status ${v.statusCode}: ${C.slice(0,150)}`),h({retry:!0,reason:"status_"+v.statusCode,message:C})});return}if(p){if(r){n.writeHead(200,{"Content-Type":"text/event-stream; charset=utf-8","Cache-Control":"no-cache",Connection:"keep-alive"});let C=new $t(b);return v.pipe(C).pipe(n),h({done:!0})}if(d){n.writeHead(200,{"Content-Type":"text/event-stream; charset=utf-8","Cache-Control":"no-cache",Connection:"keep-alive"});let C=new Gn;return v.pipe(C).pipe(n),h({done:!0})}return n.writeHead(200,v.headers),v.pipe(n),h({done:!0})}let an=[];v.on("data",(C)=>an.push(C)),v.on("end",()=>{let C=Buffer.concat(an).toString("utf8"),D=Ot(C);if(r)return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify(_t(D,b))),h({done:!0});if(d){let ot=C.split(`
`),mn=[],xn="STOP",hn=void 0;for(let M of ot){let vn=M.trim();if(vn.startsWith("data:")){let ln=vn.slice(5).trim();if(!ln||ln==="[DONE]")continue;try{let sn=JSON.parse(ln),rn=sn.response||sn;if(rn.usageMetadata)hn=rn.usageMetadata;let K=rn.candidates||[];if(K[0]){if(K[0].finishReason)xn=K[0].finishReason;let at=K[0].content?.parts||[];for(let it of at)mn.push(it)}}catch(sn){}}}let _=[],B="";for(let M of mn)if(M.text&&!M.thought)B+=M.text;else if(M.functionCall){if(B)_.push({text:B}),B="";_.push(M)}else if(!M.thought)_.push(M);if(B)_.push({text:B});if(_.length===0)_=[{text:D||"Done."}];return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({candidates:[{content:{role:"model",parts:_},finishReason:xn}],usageMetadata:hn})),h({done:!0})}return n.writeHead(200,v.headers),n.end(Buffer.concat(an)),h({done:!0})})});Q.on("timeout",()=>{Q.destroy(Error("TIMEOUT")),h({retry:!0,reason:"TIMEOUT"})}),Q.on("error",(v)=>{h({retry:!0,reason:v.message})}),Q.write(u),Q.end()});if(N.done)return;y=N}n.writeHead(503,{"Content-Type":"application/json"}),n.end(JSON.stringify({error:{code:503,message:"All accounts in pool are currently exhausted or cooling down. Please retry shortly.",status:"UNAVAILABLE",details:y?.message||null}}))}Yn.exports={handleAiProxyRequest:Pt}});var Zn=L((ae,Xn)=>{var Qn=g("http"),Wn=g("https"),oe=g("url"),Yt=R();function tn(){return Yt.getProviders()}async function Ft(t){let n=tn().ollama||{},l=(t||n.host||"http://127.0.0.1:11434").replace(/\/+$/,"");try{let a=new URL("/api/tags",l),e=a.protocol==="https:"?Wn:Qn;return new Promise((o)=>{let r=e.request(a.toString(),{method:"GET",timeout:2500},(i)=>{let d="";i.on("data",(c)=>d+=c),i.on("end",()=>{try{let s=(JSON.parse(d).models||[]).map((p)=>p.name);o({success:!0,online:!0,models:s,count:s.length})}catch(c){o({success:!0,online:!0,models:[],count:0})}})});r.on("timeout",()=>{r.destroy(),o({success:!1,online:!1,error:"Connection timed out"})}),r.on("error",(i)=>o({success:!1,online:!1,error:i.message})),r.end()})}catch(a){return{success:!1,online:!1,error:a.message}}}async function Qt(t,n){let l=tn()["9router"]||{},a=(t||l.host||"http://127.0.0.1:20128").replace(/\/+$/,""),e=n!==void 0?n:l.api_key||"";try{let o=new URL("/v1/models",a),r=o.protocol==="https:"?Wn:Qn,i={};if(e)i.Authorization=`Bearer ${e}`;return new Promise((d)=>{let c=r.request(o.toString(),{method:"GET",headers:i,timeout:3000},(s)=>{let p="";s.on("data",(b)=>p+=b),s.on("end",()=>{try{let b=JSON.parse(p),E=(Array.isArray(b.data)?b.data:Array.isArray(b)?b:[]).map((w)=>w.id||w.name);d({success:!0,online:!0,models:E,count:E.length})}catch(b){d({success:!0,online:!0,models:[],count:0})}})});c.on("timeout",()=>{c.destroy(),d({success:!1,online:!1,error:"Connection timed out"})}),c.on("error",(s)=>d({success:!1,online:!1,error:s.message})),c.end()})}catch(o){return{success:!1,online:!1,error:o.message}}}Xn.exports={get DEFAULT_PROVIDERS(){return tn()},getProviders:tn,testOllamaConnectivity:Ft,test9RouterConnectivity:Qt}});var Dn=L((ie,Jn)=>{Jn.exports={indexHtml:`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MrFlow \u2014 Sovereign Connector & Multi-Provider Matrix</title>
    <link rel="stylesheet" href="style.css?v=2.17">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="matrix-bg"></div>

    <!-- Sovereign Gate Lock Screen (Visible when not authenticated) -->
    <div id="sovereign-gate-lock" class="gate-lock-overlay hidden">
        <div class="gate-lock-card">
            <div class="gate-lock-icon-wrap">
                <div class="gate-lock-icon">\uD83D\uDD12</div>
                <div class="gate-lock-ring"></div>
            </div>
            <div class="gate-lock-badge">SOVEREIGN QUARANTINE GATE</div>
            <h2 class="gate-lock-title">ROUTER ACCESS LOCKED</h2>
            <p class="gate-lock-desc">
                Sovereign AI Router is synchronized with <strong>auth.floworkos.com</strong>.
                Connect with your Flowork OS account to unlock inference, activate the quota shield, and restore your Cloud Vault accounts.
            </p>

            <div class="gate-lock-actions">
                <button id="btn-lock-login" class="btn btn-primary btn-large btn-glow">
                    <span class="btn-icon">\uD83D\uDD17</span>
                    <span>Connect to Flowork OS</span>
                </button>
            </div>

            <div class="gate-lock-divider">
                <span>or paste session token</span>
            </div>

            <div class="gate-lock-token-input">
                <input type="password" id="input-manual-token" placeholder="Paste flowork_token here..." autocomplete="off">
                <button id="btn-submit-token" class="btn btn-secondary">Submit</button>
            </div>

            <div class="gate-lock-status" id="lock-status-txt">
                Awaiting authentication session...
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="app-container" id="app-main">
        <!-- Header -->
        <header class="app-header">
            <div class="header-left">
                <div class="logo-badge">
                    <span class="logo-icon">\u26A1</span>
                    <span class="logo-pulse"></span>
                </div>
                <div class="title-group">
                    <div class="title-row">
                        <h1 class="main-title">SOVEREIGN ROUTER</h1>
                        <span class="version-tag">v2.16 MESH</span>
                    </div>
                    <p class="subtitle">Multi-Account Quota Shield & Provider Switchboard</p>
                </div>
            </div>

            <div class="header-right">
                <!-- Connect Button (Shown when not authenticated) -->
                <button id="btn-header-connect" class="btn btn-header-connect">
                    <span class="btn-icon">\uD83D\uDD17</span>
                    <span>Connect to Flowork OS</span>
                </button>

                <!-- User Session Badge (Shown when authenticated) -->
                <div class="user-session-badge" id="user-badge" style="display: none;">
                    <span class="user-avatar" id="user-avatar">\uD83D\uDC64</span>
                    <span class="user-name" id="user-name">@operator</span>
                    <button id="btn-logout" class="btn-logout" title="Sign Out from auth.floworkos.com">\u2715</button>
                </div>

                <div class="connection-status" id="system-status-pill">
                    <span class="status-dot"></span>
                    <span class="status-label" id="system-status-text">MATRIX ONLINE // :9099</span>
                </div>
            </div>
        </header>

        <!-- AI Provider Switcher Strip (Connector / Ollama / 9Router) -->
        <section class="provider-switchboard">
            <div class="provider-switch-header">
                <span class="switch-label">SELECT ACTIVE INFERENCE ENGINE:</span>
                <span class="active-provider-badge" id="current-provider-tag">\u26A1 SOVEREIGN CONNECTOR</span>
            </div>
            <div class="provider-tabs">
                <button class="provider-tab active" data-provider="connector" id="tab-prov-connector">
                    <span class="prov-icon">\u26A1</span>
                    <div class="prov-meta">
                        <span class="prov-title">Sovereign Connector</span>
                        <span class="prov-sub">Google Pro Multi-Account Rotator</span>
                    </div>
                </button>

                <button class="provider-tab" data-provider="ollama" id="tab-prov-ollama">
                    <span class="prov-icon">\uD83E\uDD99</span>
                    <div class="prov-meta">
                        <span class="prov-title">Ollama Local</span>
                        <span class="prov-sub">Offline Local GPU Engine</span>
                    </div>
                </button>

                <button class="provider-tab" data-provider="9router" id="tab-prov-9router">
                    <span class="prov-icon">\uD83D\uDD00</span>
                    <div class="prov-meta">
                        <span class="prov-title">9Router Gateway</span>
                        <span class="prov-sub">Universal Model Proxy</span>
                    </div>
                </button>
            </div>
        </section>

        <!-- ======================================================== -->
        <!-- VIEW 1: SOVEREIGN CONNECTOR (Google Multi-Account Pool)  -->
        <!-- ======================================================== -->
        <div id="view-connector" class="provider-view">
            <!-- Metric Cards Grid -->
            <section class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">TOTAL ACCOUNTS</span>
                        <span class="metric-icon">\uD83D\uDC65</span>
                    </div>
                    <div class="metric-body">
                        <span class="metric-value highlight" id="stat-total">0</span>
                        <span class="metric-unit" id="stat-max">/ 50 max</span>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">ACTIVE PRIMARY</span>
                        <span class="metric-icon">\u2B50</span>
                    </div>
                    <div class="metric-body">
                        <span class="metric-value active-email" id="stat-active-email" title="No account active">None</span>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">POOL HEALTH</span>
                        <span class="metric-icon">\uD83D\uDEE1\uFE0F</span>
                    </div>
                    <div class="metric-body">
                        <span class="metric-value health" id="stat-health">0 Ready</span>
                        <span class="metric-sub" id="stat-cooldown-sub">0 in cooldown</span>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">ROTATION STRATEGY</span>
                        <span class="metric-icon">\u2699\uFE0F</span>
                    </div>
                    <div class="metric-body select-wrap">
                        <select id="strategy-select" class="strategy-dropdown">
                            <option value="failover">Failover on Limit (Sticky)</option>
                            <option value="round_robin">Round Robin (Cyclic)</option>
                            <option value="least_used">Least Used (Balanced)</option>
                            <option value="random">Randomized</option>
                        </select>
                    </div>
                </div>
            </section>

            <!-- Actions & Controls Bar -->
            <section class="action-bar">
                <div class="action-left">
                    <button id="btn-sync-cloud" class="btn btn-cloud">
                        <span class="btn-icon">\u2601\uFE0F</span>
                        <span>Unduh Akun (Sync Cloud)</span>
                    </button>
                    <button id="btn-add-account" class="btn btn-primary">
                        <span class="btn-icon">\u2795</span>
                        <span>Add Google Account</span>
                    </button>
                    <button id="btn-refresh-pool" class="btn btn-secondary">
                        <span class="btn-icon">\uD83D\uDD04</span>
                        <span>Refresh</span>
                    </button>
                    <button id="btn-clear-cooldown" class="btn btn-tertiary">
                        <span class="btn-icon">\u26A1</span>
                        <span>Clear Cooldowns</span>
                    </button>
                </div>

                <div class="action-right">
                    <div class="search-box">
                        <span class="search-icon">\uD83D\uDD0D</span>
                        <input type="text" id="account-search-input" placeholder="Search by email..." autocomplete="off">
                        <button id="search-clear-btn" class="search-clear hidden">&times;</button>
                    </div>
                </div>
            </section>

            <!-- Filter Tabs -->
            <div class="filter-strip">
                <div class="filter-tabs">
                    <button class="filter-tab active" data-filter="all">
                        <span>All Accounts</span>
                        <span class="tab-badge" id="tab-cnt-all">0</span>
                    </button>
                    <button class="filter-tab" data-filter="active">
                        <span>Active</span>
                        <span class="tab-badge" id="tab-cnt-active">0</span>
                    </button>
                    <button class="filter-tab" data-filter="ready">
                        <span>Ready</span>
                        <span class="tab-badge" id="tab-cnt-ready">0</span>
                    </button>
                    <button class="filter-tab" data-filter="cooldown">
                        <span>Cooldown</span>
                        <span class="tab-badge" id="tab-cnt-cooldown">0</span>
                    </button>
                </div>
            </div>

            <!-- Accounts Container -->
            <main class="accounts-section">
                <div id="accounts-list" class="accounts-list">
                    <div class="empty-state">
                        <div class="empty-icon">\uD83D\uDD00</div>
                        <h3>Loading Account Pool...</h3>
                        <p>Fetching active session matrix from server</p>
                    </div>
                </div>
            </main>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 2: OLLAMA LOCAL ENGINE                              -->
        <!-- ======================================================== -->
        <div id="view-ollama" class="provider-view hidden">
            <div class="provider-panel">
                <div class="panel-header">
                    <div class="panel-title-wrap">
                        <span class="panel-icon">\uD83E\uDD99</span>
                        <div>
                            <h3 class="panel-title">Ollama Local Engine</h3>
                            <p class="panel-desc">Offline local inference served through your hardware GPU / NPU.</p>
                        </div>
                    </div>
                    <div class="panel-status-pill" id="ollama-ping-pill">
                        <span class="status-dot"></span>
                        <span id="ollama-ping-txt">Checking...</span>
                    </div>
                </div>

                <div class="panel-form-grid">
                    <div class="form-group">
                        <label>Ollama Server Endpoint</label>
                        <div class="input-with-button">
                            <input type="text" id="input-ollama-host" placeholder="http://127.0.0.1:11434" value="http://127.0.0.1:11434">
                            <button id="btn-test-ollama" class="btn btn-secondary">\u26A1 Test Host</button>
                        </div>
                        <span class="form-hint">Default local daemon runs on <code>http://127.0.0.1:11434</code></span>
                    </div>

                    <div class="form-group">
                        <div class="label-with-action">
                            <label>Active Ollama Model</label>
                            <span class="label-sub">Ketik manual nama model</span>
                        </div>
                        <div class="input-with-button">
                            <input type="text" id="input-ollama-model" placeholder="deepseek-v4-9b-uncensored:latest" value="deepseek-v4-9b-uncensored:latest">
                            <button id="btn-add-ollama-model" class="btn btn-secondary" type="button" title="Simpan ke daftar preset">+ Simpan Preset</button>
                        </div>
                        <div class="models-chips-wrap">
                            <span class="chips-title">Preset Models (Klik untuk memilih):</span>
                            <div id="ollama-models-chips" class="models-chips"></div>
                        </div>
                        <span class="form-hint">Model ini yang akan menerima seluruh panggilan autonomous agent. Bebas ketik model apa saja.</span>
                    </div>
                </div>

                <div class="panel-actions">
                    <button id="btn-save-ollama" class="btn btn-primary">
                        <span>\uD83D\uDCBE Save & Activate Ollama</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 3: 9ROUTER UNIVERSAL GATEWAY                        -->
        <!-- ======================================================== -->
        <div id="view-9router" class="provider-view hidden">
            <div class="provider-panel">
                <div class="panel-header">
                    <div class="panel-title-wrap">
                        <span class="panel-icon">\uD83D\uDD00</span>
                        <div>
                            <h3 class="panel-title">9Router Universal Gateway</h3>
                            <p class="panel-desc">Universal proxy gateway with multi-upstream dynamic model routing.</p>
                        </div>
                    </div>
                    <div class="panel-status-pill" id="9router-ping-pill">
                        <span class="status-dot"></span>
                        <span id="9router-ping-txt">Checking...</span>
                    </div>
                </div>

                <div class="panel-form-grid">
                    <div class="form-group">
                        <label>9Router Gateway Endpoint</label>
                        <div class="input-with-button">
                            <input type="text" id="input-9router-host" placeholder="http://127.0.0.1:20128" value="http://127.0.0.1:20128">
                            <button id="btn-test-9router" class="btn btn-secondary">\u26A1 Test Gateway</button>
                        </div>
                        <span class="form-hint">Local instance or cloud gateway (e.g. <code>https://api.9router.com/v1</code>)</span>
                    </div>

                    <div class="form-group">
                        <label>Gateway API Key (Optional)</label>
                        <input type="password" id="input-9router-key" placeholder="Bearer token or leave empty if no auth required">
                        <span class="form-hint">Required for authenticated 9Router relays or cloud gateways.</span>
                    </div>

                    <div class="form-group">
                        <div class="label-with-action">
                            <label>Routed Target Model</label>
                            <span class="label-sub">Ketik manual nama model</span>
                        </div>
                        <div class="input-with-button">
                            <input type="text" id="input-9router-model" placeholder="Ketik model manual (contoh: clinepass/cline-pass/glm-5.2, deepseek/deepseek-r1...)" value="clinepass/cline-pass/glm-5.2">
                            <button id="btn-add-9router-model" class="btn btn-secondary" type="button" title="Simpan ke daftar preset">+ Simpan Preset</button>
                        </div>
                        <div class="models-chips-wrap">
                            <span class="chips-title">Preset Models (Klik untuk memilih):</span>
                            <div id="9router-models-chips" class="models-chips"></div>
                        </div>
                        <span class="form-hint">Model identifier upstream yang dituju oleh gateway 9Router. Bebas ketik model apa saja.</span>
                    </div>
                </div>

                <div class="panel-actions">
                    <button id="btn-save-9router" class="btn btn-primary">
                        <span>\uD83D\uDCBE Save & Activate 9Router</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="app-footer">
            <div class="footer-info">
                <span>Binding: <strong id="footer-host">127.0.0.1:9099</strong></span>
                <span class="divider">\u2022</span>
                <span>Active Provider: <strong class="text-cyan" id="footer-active-provider">Sovereign Connector</strong></span>
                <span class="divider">\u2022</span>
                <span>Auth Portal: <strong class="text-cyan">auth.floworkos.com</strong></span>
                <span class="divider">\u2022</span>
                <span>Gateway Status: <span class="text-green">Proxy Online</span></span>
            </div>
            <div class="footer-meta">
                <span>MrFlow Sovereign Mesh</span>
            </div>
        </footer>
    </div>

    <!-- Toast Notification Container -->
    <div id="toast-container" class="toast-container"></div>

    <script src="app.js?v=2.18"></script>
</body>
</html>
`,styleCss:`:root {
    --bg-base: #0a1422;
    --bg-card: rgba(255, 255, 255, 0.07);
    --bg-card-hover: rgba(255, 255, 255, 0.12);
    --border-color: rgba(255, 255, 255, 0.16);
    --border-hover: rgba(56, 189, 248, 0.5);
    --cyan: #38bdf8;
    --cyan-dim: #0284c7;
    --cyan-glow: rgba(56, 189, 248, 0.3);
    --emerald: #10b981;
    --emerald-glow: rgba(16, 185, 129, 0.3);
    --red: #ef4444;
    --red-glow: rgba(239, 68, 68, 0.3);
    --amber: #f59e0b;
    --text-main: #f8fafc;
    --text-sub: #cbd5e1;
    --text-muted: #94a3b8;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: var(--bg-base);
    color: var(--text-main);
    font-family: var(--font-sans);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow-x: hidden;
    padding: 24px 16px;
}

/* Futuristic background glow */
.matrix-bg {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(circle at 15% 15%, rgba(0, 229, 255, 0.05) 0%, transparent 45%),
        radial-gradient(circle at 85% 20%, rgba(16, 185, 129, 0.04) 0%, transparent 40%),
        radial-gradient(circle at 50% 80%, rgba(2, 132, 199, 0.06) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* \u2500\u2500 \uD83D\uDD12 Sovereign Gate Quarantine Lock Overlay \u2500\u2500 */
.gate-lock-overlay {
    position: fixed;
    inset: 0;
    background: rgba(4, 8, 16, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 20px;
    animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.gate-lock-card {
    background: #0d1527;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 24px;
    padding: 38px 36px;
    max-width: 500px;
    width: 100%;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.9), 0 0 35px rgba(239, 68, 68, 0.2);
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;
}

.gate-lock-icon-wrap {
    position: relative;
    width: 64px;
    height: 64px;
    border-radius: 18px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin-bottom: 16px;
}

.gate-lock-ring {
    position: absolute;
    inset: -3px;
    border-radius: 20px;
    border: 1.5px solid var(--red);
    opacity: 0.5;
    animation: pulse 2s infinite;
}

.gate-lock-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 800;
    color: var(--red);
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: 3px 12px;
    border-radius: 999px;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
}

.gate-lock-title {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.04em;
    margin-bottom: 10px;
}

.gate-lock-desc {
    font-size: 13px;
    color: var(--text-sub);
    line-height: 1.6;
    margin-bottom: 24px;
}

.gate-lock-desc strong {
    color: var(--cyan);
}

.btn-large {
    padding: 12px 28px;
    font-size: 13.5px;
    font-weight: 800;
    border-radius: 999px;
}

.btn-glow {
    background: linear-gradient(135deg, #0284c7 0%, #00e5ff 100%);
    color: #ffffff;
    box-shadow: 0 6px 24px rgba(0, 229, 255, 0.45);
}

.btn-glow:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 229, 255, 0.65);
}

.gate-lock-divider {
    display: flex;
    align-items: center;
    width: 100%;
    margin: 20px 0 14px 0;
    font-size: 11px;
    color: var(--text-muted);
}

.gate-lock-divider::before, .gate-lock-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
}

.gate-lock-divider span {
    padding: 0 12px;
}

.gate-lock-token-input {
    display: flex;
    gap: 8px;
    width: 100%;
    margin-bottom: 16px;
}

.gate-lock-token-input input {
    flex: 1;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 8px 12px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: #ffffff;
    outline: none;
}

.gate-lock-token-input input:focus {
    border-color: var(--cyan);
}

.gate-lock-status {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
}

/* \u2500\u2500 Main App Container \u2500\u2500 */
.app-container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 980px;
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 229, 255, 0.1);
    padding: 16px 24px 24px 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* \u2500\u2500 Desktop Header Integrated Menubar with Cyberpunk Blinking \u2500\u2500 */
.header-menu-container {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(10, 16, 30, 0.85);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 12px;
    padding: 4px 10px;
    box-shadow: 0 0 18px rgba(0, 229, 255, 0.15);
    animation: menubarBreath 2.8s infinite ease-in-out;
    position: relative;
    z-index: 100;
}

.header-blink-beacon {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 6px;
    user-select: none;
}

.blink-dot-beacon {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00e5ff;
    box-shadow: 0 0 8px #00e5ff, 0 0 16px rgba(0, 229, 255, 0.9);
    animation: cyberDotBlink 1.2s infinite ease-in-out;
}

.blink-live-text {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 800;
    color: #00e5ff;
    letter-spacing: 0.06em;
    animation: cyberTextBlink 1.2s infinite ease-in-out;
}

.header-menubar {
    display: flex;
    align-items: center;
    gap: 3px;
}

.menubar-item {
    position: relative;
}

.menubar-btn.blink-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: transparent;
    border: none;
    color: var(--text-sub);
    font-size: 11.5px;
    font-weight: 600;
    padding: 5px 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    font-family: var(--font-sans);
    outline: none;
}

.menubar-btn.blink-item:hover,
.menubar-btn.blink-item.active {
    background: rgba(0, 229, 255, 0.15);
    color: #ffffff;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.3);
}

.btn-blink-pulse {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--cyan);
    opacity: 0.8;
    animation: miniDotBlink 1.6s infinite ease-in-out;
}

/* Stagger mini dot blinks */
.menubar-item:nth-child(2) .btn-blink-pulse { animation-delay: 0.3s; }
.menubar-item:nth-child(3) .btn-blink-pulse { animation-delay: 0.6s; }
.menubar-item:nth-child(4) .btn-blink-pulse { animation-delay: 0.9s; }
.menubar-item:nth-child(5) .btn-blink-pulse { animation-delay: 1.2s; }

/* \u2500\u2500 Cyber Blinking Keyframes \u2500\u2500 */
@keyframes cyberDotBlink {
    0%, 100% {
        opacity: 1;
        transform: scale(1.15);
        box-shadow: 0 0 10px #00e5ff, 0 0 20px rgba(0, 229, 255, 0.9);
        background: #00e5ff;
    }
    50% {
        opacity: 0.2;
        transform: scale(0.75);
        box-shadow: 0 0 2px #00e5ff;
        background: #0284c7;
    }
}

@keyframes cyberTextBlink {
    0%, 100% {
        opacity: 1;
        text-shadow: 0 0 8px rgba(0, 229, 255, 0.9), 0 0 16px rgba(0, 229, 255, 0.6);
        color: #00e5ff;
    }
    50% {
        opacity: 0.35;
        text-shadow: none;
        color: #38bdf8;
    }
}

@keyframes miniDotBlink {
    0%, 100% {
        opacity: 0.9;
        box-shadow: 0 0 6px #00e5ff;
        transform: scale(1);
    }
    50% {
        opacity: 0.15;
        box-shadow: none;
        transform: scale(0.6);
    }
}

@keyframes menubarBreath {
    0%, 100% {
        border-color: rgba(0, 229, 255, 0.6);
        box-shadow: 0 0 18px rgba(0, 229, 255, 0.3);
    }
    50% {
        border-color: rgba(0, 229, 255, 0.18);
        box-shadow: 0 0 4px rgba(0, 229, 255, 0.05);
    }
}

.blink-badge {
    animation: badgeBlink 2s infinite ease-in-out;
}

@keyframes badgeBlink {
    0%, 100% {
        opacity: 1;
        border-color: rgba(0, 229, 255, 0.65);
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    50% {
        opacity: 0.45;
        border-color: rgba(0, 229, 255, 0.2);
        box-shadow: none;
    }
}

.menubar-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    min-width: 250px;
    background: rgba(10, 16, 30, 0.96);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 10px;
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 229, 255, 0.15);
    padding: 6px;
    display: none;
    flex-direction: column;
    gap: 2px;
    z-index: 999;
    animation: fadeIn 0.15s ease;
}

.menubar-dropdown.show {
    display: flex !important;
}

.menu-item {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 7px 10px;
    border: none;
    background: transparent;
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 500;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.12s ease;
    text-align: left;
    font-family: var(--font-sans);
}

.menu-item:hover {
    background: rgba(0, 229, 255, 0.15);
    color: var(--cyan);
}

.menu-icon {
    font-size: 13px;
    margin-right: 8px;
    width: 16px;
    display: inline-block;
}

.menu-text {
    flex: 1;
}

.menu-shortcut {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 5px;
    border-radius: 4px;
    margin-left: 10px;
}

.menu-check {
    font-size: 12px;
    color: var(--cyan);
    font-weight: bold;
    margin-left: 8px;
    width: 14px;
    text-align: right;
}

.menu-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 4px 2px;
}

.os-mesh-badge {
    font-size: 10.5px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    letter-spacing: 0.04em;
}

.about-card {
    max-width: 440px !important;
}

.about-meta-grid {
    margin-top: 14px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 11.5px;
}

.meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--text-sub);
}

.meta-row strong {
    color: #ffffff;
}

.meta-row code {
    color: var(--cyan);
    font-family: var(--font-mono);
    font-size: 10.5px;
}

/* \u2500\u2500 Header \u2500\u2500 */
.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-left {
    display: flex;
    align-items: center;
    gap: 14px;
}

.logo-badge {
    position: relative;
    width: 44px;
    height: 44px;
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 20px var(--cyan-glow);
}

.logo-pulse {
    position: absolute;
    inset: -2px;
    border-radius: 14px;
    border: 1px solid var(--cyan);
    opacity: 0.4;
    animation: pulse 2.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.98); opacity: 0.6; }
    50% { transform: scale(1.08); opacity: 0; }
    100% { transform: scale(0.98); opacity: 0; }
}

.title-group {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.title-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.main-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.05em;
    background: linear-gradient(135deg, #ffffff 40%, var(--cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.version-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    color: var(--cyan);
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.3);
    padding: 2px 7px;
    border-radius: 999px;
    letter-spacing: 0.04em;
}

.subtitle {
    font-size: 12px;
    color: var(--text-sub);
}

.header-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Header Connect Button (Active when not logged in) */
.btn-header-connect {
    background: linear-gradient(135deg, #0284c7 0%, #00e5ff 100%);
    color: #ffffff;
    font-family: var(--font-sans);
    font-size: 11.5px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 2px 12px rgba(0, 229, 255, 0.4);
    animation: gentleGlow 2s infinite alternate;
}

@keyframes gentleGlow {
    from { box-shadow: 0 0 8px rgba(0, 229, 255, 0.3); }
    to { box-shadow: 0 0 16px rgba(0, 229, 255, 0.6); }
}

.btn-header-connect:hover {
    transform: translateY(-1px);
}

.user-session-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0, 229, 255, 0.08);
    border: 1px solid rgba(0, 229, 255, 0.3);
    padding: 5px 12px;
    border-radius: 999px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--cyan);
}

.user-avatar {
    font-size: 13px;
}

.user-name {
    font-weight: 700;
}

.btn-logout {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 12px;
    cursor: pointer;
    margin-left: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn-logout:hover {
    color: var(--red);
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 6px 14px;
    border-radius: 999px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--emerald);
}

.status-dot {
    width: 8px;
    height: 8px;
    background-color: var(--emerald);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--emerald);
}

/* \u2500\u2500 \u26A1 AI Provider Switchboard Strip \u2500\u2500 */
.provider-switchboard {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.provider-switch-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.switch-label {
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: var(--text-sub);
}

.active-provider-badge {
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 700;
    color: var(--cyan);
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.3);
    padding: 2px 10px;
    border-radius: 999px;
}

.provider-tabs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.provider-tab {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    color: var(--text-main);
}

.provider-tab:hover {
    background: rgba(18, 30, 52, 0.9);
    border-color: var(--border-hover);
    transform: translateY(-1px);
}

.provider-tab.active {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(0, 229, 255, 0.12) 100%);
    border-color: var(--cyan);
    box-shadow: 0 0 16px var(--cyan-glow);
}

.prov-icon {
    font-size: 24px;
}

.prov-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.prov-title {
    font-size: 13px;
    font-weight: 800;
    color: #ffffff;
}

.provider-tab.active .prov-title {
    color: var(--cyan);
}

.prov-sub {
    font-size: 10px;
    color: var(--text-muted);
}

/* \u2500\u2500 Panels for Ollama & 9Router \u2500\u2500 */
.provider-panel {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 22px 24px;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}

.panel-icon {
    font-size: 28px;
}

.panel-title {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
}

.panel-desc {
    font-size: 12px;
    color: var(--text-sub);
}

.panel-status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-muted);
}

.panel-status-pill.online {
    background: rgba(16, 185, 129, 0.12);
    border-color: rgba(16, 185, 129, 0.35);
    color: var(--emerald);
}

.panel-status-pill.offline {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.35);
    color: #f87171;
}

.panel-form-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.form-group label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--text-sub);
}

.form-group input, .panel-form-grid select {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 8px 12px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: #ffffff;
    outline: none;
    transition: all 0.15s ease;
}

.form-group input:focus, .panel-form-grid select:focus {
    border-color: var(--cyan);
    box-shadow: 0 0 10px var(--cyan-glow);
}

.form-hint {
    font-size: 10.5px;
    color: var(--text-muted);
}

.form-hint code {
    color: var(--cyan);
    font-family: var(--font-mono);
}

.input-with-button {
    display: flex;
    gap: 8px;
}

.input-with-button input {
    flex: 1;
}

/* \u2500\u2500 Custom Model Input & Chips \u2500\u2500 */
.label-with-action {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
}

.label-sub {
    font-size: 11px;
    color: var(--cyan);
    font-weight: 500;
    opacity: 0.85;
}

.models-chips-wrap {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.chips-title {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.models-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 30px;
}

.model-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--text-sub);
    font-family: var(--font-mono);
    font-size: 11.5px;
    padding: 5px 10px;
    border-radius: 7px;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
}

.model-chip:hover {
    border-color: var(--cyan);
    color: #ffffff;
    background: rgba(0, 229, 255, 0.08);
    transform: translateY(-1px);
}

.model-chip.active {
    background: rgba(0, 229, 255, 0.16);
    border-color: var(--cyan);
    color: var(--cyan);
    font-weight: 700;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.25);
}

.model-chip .chip-name {
    cursor: pointer;
}

.model-chip .chip-remove {
    font-size: 13px;
    line-height: 1;
    color: var(--text-muted);
    border-radius: 4px;
    padding: 1px 4px;
    transition: all 0.15s ease;
}

.model-chip .chip-remove:hover {
    background: rgba(239, 68, 68, 0.25);
    color: #f87171;
}

.panel-actions {
    display: flex;
    justify-content: flex-end;
}

/* \u2500\u2500 Metrics Grid \u2500\u2500 */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.metric-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--text-sub);
}

.metric-icon {
    font-size: 14px;
    opacity: 0.8;
}

.metric-body {
    display: flex;
    align-items: baseline;
    gap: 6px;
    overflow: hidden;
}

.metric-value.highlight {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
}

.metric-unit {
    font-size: 11px;
    color: var(--text-muted);
    font-family: var(--font-mono);
}

.metric-value.active-email {
    font-size: 13px;
    font-weight: 700;
    color: var(--cyan);
    font-family: var(--font-mono);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: default;
}

.metric-value.health {
    font-size: 16px;
    font-weight: 700;
    color: var(--emerald);
}

.metric-sub {
    font-size: 10.5px;
    color: var(--text-muted);
}

.strategy-dropdown {
    width: 100%;
    background: rgba(0, 229, 255, 0.05);
    border: 1px solid rgba(0, 229, 255, 0.3);
    color: var(--cyan);
    font-family: var(--font-sans);
    font-size: 11.5px;
    font-weight: 700;
    border-radius: 8px;
    padding: 5px 8px;
    outline: none;
    cursor: pointer;
    transition: all 0.15s ease;
}

.strategy-dropdown:focus {
    border-color: var(--cyan);
    box-shadow: 0 0 10px var(--cyan-glow);
}

.strategy-dropdown option {
    background: #0f172a;
    color: #ffffff;
}

/* \u2500\u2500 Actions Bar \u2500\u2500 */
.action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.action-left {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    outline: none;
    border: none;
}

.btn-cloud {
    background: linear-gradient(135deg, #0284c7 0%, #00e5ff 100%);
    color: #ffffff;
    box-shadow: 0 4px 16px rgba(0, 229, 255, 0.35);
}

.btn-cloud:hover {
    transform: translateY(-1.5px);
    box-shadow: 0 6px 22px rgba(0, 229, 255, 0.55);
}

.btn-primary {
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #34d399;
}

.btn-primary:hover {
    background: rgba(16, 185, 129, 0.28);
    border-color: var(--emerald);
    transform: translateY(-1.5px);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--text-main);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.25);
}

.btn-tertiary {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #fcd34d;
}

.btn-tertiary:hover {
    background: rgba(245, 158, 11, 0.2);
    border-color: rgba(245, 158, 11, 0.5);
}

.btn:active {
    transform: translateY(0);
}

.btn-icon {
    font-size: 13px;
}

.search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--border-color);
    border-radius: 999px;
    padding: 6px 14px;
    width: 240px;
    transition: all 0.2s ease;
}

.search-box:focus-within {
    border-color: var(--cyan);
    box-shadow: 0 0 12px var(--cyan-glow);
    width: 280px;
}

.search-icon {
    font-size: 12px;
    color: var(--text-muted);
}

.search-box input {
    background: transparent;
    border: none;
    outline: none;
    font-family: var(--font-sans);
    font-size: 12px;
    color: #ffffff;
    width: 100%;
}

.search-box input::placeholder {
    color: var(--text-muted);
}

.search-clear {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 16px;
    cursor: pointer;
    line-height: 1;
}

.search-clear:hover {
    color: #ffffff;
}

.hidden {
    display: none !important;
}

/* \u2500\u2500 Filter Strip \u2500\u2500 */
.filter-strip {
    display: flex;
    align-items: center;
}

.filter-tabs {
    display: flex;
    gap: 8px;
}

.filter-tab {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-sub);
    font-family: var(--font-sans);
    font-size: 11.5px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 999px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s ease;
}

.filter-tab:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #ffffff;
}

.filter-tab.active {
    background: #0284c7;
    border-color: #0284c7;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(2, 132, 199, 0.4);
}

.tab-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    background: rgba(0, 0, 0, 0.35);
    padding: 1px 6px;
    border-radius: 999px;
}

/* \u2500\u2500 Accounts List \u2500\u2500 */
.accounts-section {
    min-height: 240px;
    max-height: 480px;
    overflow-y: auto;
    padding-right: 4px;
}

.accounts-section::-webkit-scrollbar {
    width: 6px;
}

.accounts-section::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 8px;
}

.accounts-section::-webkit-scrollbar-thumb {
    background: rgba(0, 229, 255, 0.2);
    border-radius: 8px;
}

.accounts-section::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 229, 255, 0.4);
}

.accounts-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.account-card {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.account-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-hover);
    transform: translateX(2px);
}

.account-card.is-active {
    border-color: rgba(16, 185, 129, 0.45);
    background: rgba(16, 185, 129, 0.06);
    box-shadow: 0 0 16px rgba(16, 185, 129, 0.1);
}

.account-card.is-cooldown {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.04);
}

.acc-left {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
}

.acc-index {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    min-width: 20px;
}

.acc-avatar {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: #ffffff;
    font-size: 14px;
    flex-shrink: 0;
}

.account-card.is-active .acc-avatar {
    border-color: var(--emerald);
    color: var(--emerald);
    box-shadow: 0 0 10px var(--emerald-glow);
}

.acc-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.acc-email-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.acc-email {
    font-size: 13.5px;
    font-weight: 700;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.acc-badge {
    font-family: var(--font-mono);
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    letter-spacing: 0.05em;
    flex-shrink: 0;
}

.acc-badge.badge-active {
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--emerald);
    box-shadow: 0 0 10px var(--emerald-glow);
}

.acc-badge.badge-ready {
    background: rgba(100, 116, 139, 0.2);
    border: 1px solid rgba(100, 116, 139, 0.35);
    color: var(--text-sub);
}

.acc-badge.badge-limit {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #f87171;
    box-shadow: 0 0 10px var(--red-glow);
}

.acc-meta {
    display: flex;
    gap: 12px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
}

.acc-meta-item span {
    color: var(--text-sub);
}

.acc-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.btn-card {
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    transition: all 0.15s ease;
}

.btn-card-active {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: var(--emerald);
    cursor: default;
}

.btn-card-select {
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.25);
    color: var(--cyan);
}

.btn-card-select:hover {
    background: rgba(0, 229, 255, 0.2);
    border-color: var(--cyan);
}

.btn-card-test {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-sub);
}

.btn-card-test:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
}

.btn-card-delete {
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-muted);
    padding: 6px 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.btn-card-delete:hover {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.3);
    color: #ef4444;
}

/* \u2500\u2500 Empty State \u2500\u2500 */
.empty-state {
    padding: 48px 24px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}

.empty-icon {
    font-size: 40px;
    margin-bottom: 6px;
    opacity: 0.8;
}

.empty-state h3 {
    font-size: 15px;
    color: #ffffff;
    font-weight: 700;
}

.empty-state p {
    font-size: 12px;
    color: var(--text-muted);
    max-width: 340px;
}

/* \u2500\u2500 Footer \u2500\u2500 */
.app-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-muted);
}

.footer-info {
    display: flex;
    align-items: center;
    gap: 8px;
}

.divider {
    opacity: 0.4;
}

.text-cyan {
    color: var(--cyan);
}

.text-green {
    color: var(--emerald);
}

/* \u2500\u2500 Toast Notifications \u2500\u2500 */
.toast-container {
    position: fixed;
    bottom: 24px;
    right: 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 10000;
    pointer-events: none;
}

.toast {
    pointer-events: auto;
    background: #0d1627;
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 12px 18px;
    font-size: 12px;
    color: #ffffff;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 15px var(--cyan-glow);
    display: flex;
    align-items: center;
    gap: 10px;
    animation: toastIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    max-width: 380px;
}

.toast.toast-success {
    border-color: rgba(16, 185, 129, 0.5);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 15px var(--emerald-glow);
}

.toast.toast-error {
    border-color: rgba(239, 68, 68, 0.5);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 15px var(--red-glow);
}

@keyframes toastIn {
    from { transform: translateY(12px) scale(0.96); opacity: 0; }
    to { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes toastOut {
    from { transform: translateY(0) scale(1); opacity: 1; }
    to { transform: translateY(12px) scale(0.96); opacity: 0; }
}
`,appJs:`// MrFlow Sovereign Connector & Account Matrix UI Controller
// Supports auth.floworkos.com login, Cloud Vault sync, and multi-provider switching (Connector, Ollama, 9Router).

(function() {
    'use strict';

    const API_BASE = window.location.origin;

    const state = {
        authenticated: false,
        user: null,
        activeProvider: 'connector',
        providers: {},
        accounts: [],
        totalAccounts: 0,
        maxAccounts: 50,
        activeAccountId: '',
        activeEmail: 'None',
        rotationMode: 'failover',
        healthyCount: 0,
        cooldownCount: 0,
        filter: 'all',
        searchQuery: '',
        isLoading: false,
        authPolling: null,
        oauthPolling: null
    };

    // DOM Elements
    const els = {
        gateLock: document.getElementById('sovereign-gate-lock'),
        btnLockLogin: document.getElementById('btn-lock-login'),
        inputManualToken: document.getElementById('input-manual-token'),
        btnSubmitToken: document.getElementById('btn-submit-token'),
        lockStatusTxt: document.getElementById('lock-status-txt'),

        btnHeaderConnect: document.getElementById('btn-header-connect'),
        userBadge: document.getElementById('user-badge'),
        userName: document.getElementById('user-name'),
        btnLogout: document.getElementById('btn-logout'),

        currentProviderTag: document.getElementById('current-provider-tag'),
        footerActiveProvider: document.getElementById('footer-active-provider'),

        // Provider views
        viewConnector: document.getElementById('view-connector'),
        viewOllama: document.getElementById('view-ollama'),
        view9Router: document.getElementById('view-9router'),

        // Ollama panel
        inputOllamaHost: document.getElementById('input-ollama-host'),
        inputOllamaModel: document.getElementById('input-ollama-model'),
        btnAddOllamaModel: document.getElementById('btn-add-ollama-model'),
        ollamaModelsChips: document.getElementById('ollama-models-chips'),
        btnTestOllama: document.getElementById('btn-test-ollama'),
        btnSaveOllama: document.getElementById('btn-save-ollama'),
        ollamaPingPill: document.getElementById('ollama-ping-pill'),
        ollamaPingTxt: document.getElementById('ollama-ping-txt'),

        // 9Router panel
        input9RouterHost: document.getElementById('input-9router-host'),
        input9RouterKey: document.getElementById('input-9router-key'),
        input9RouterModel: document.getElementById('input-9router-model'),
        btnAdd9RouterModel: document.getElementById('btn-add-9router-model'),
        r9ModelsChips: document.getElementById('9router-models-chips'),
        btnTest9Router: document.getElementById('btn-test-9router'),
        btnSave9Router: document.getElementById('btn-save-9router'),
        r9PingPill: document.getElementById('9router-ping-pill'),
        r9PingTxt: document.getElementById('9router-ping-txt'),

        // Connector metrics & controls
        statTotal: document.getElementById('stat-total'),
        statMax: document.getElementById('stat-max'),
        statActiveEmail: document.getElementById('stat-active-email'),
        statHealth: document.getElementById('stat-health'),
        statCooldownSub: document.getElementById('stat-cooldown-sub'),
        strategySelect: document.getElementById('strategy-select'),

        btnSyncCloud: document.getElementById('btn-sync-cloud'),
        btnAddAccount: document.getElementById('btn-add-account'),
        btnRefreshPool: document.getElementById('btn-refresh-pool'),
        btnClearCooldown: document.getElementById('btn-clear-cooldown'),

        searchInput: document.getElementById('account-search-input'),
        searchClearBtn: document.getElementById('search-clear-btn'),
        accountsList: document.getElementById('accounts-list'),

        tabAll: document.getElementById('tab-cnt-all'),
        tabActive: document.getElementById('tab-cnt-active'),
        tabReady: document.getElementById('tab-cnt-ready'),
        tabCooldown: document.getElementById('tab-cnt-cooldown'),

        toastContainer: document.getElementById('toast-container'),
        systemStatusText: document.getElementById('system-status-text')
    };

    // \u2500\u2500 Toast Notifications \u2500\u2500
    function showToast(message, type = 'info') {
        if (!els.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = \`toast toast-\${type}\`;
        
        let icon = '\u26A1';
        if (type === 'success') icon = '\uD83D\uDFE2';
        if (type === 'error') icon = '\u26A0\uFE0F';

        toast.innerHTML = \`
            <span>\${icon}</span>
            <span>\${escapeHtml(message)}</span>
        \`;
        els.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toastOut 0.25s forwards';
            setTimeout(() => toast.remove(), 250);
        }, 3800);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatTimeRemaining(expiresAt) {
        if (!expiresAt) return 'Session active';
        const now = Date.now();
        const diffSec = Math.floor((expiresAt - now) / 1000);
        if (diffSec <= 0) return 'Expired';
        const mins = Math.floor(diffSec / 60);
        const hours = Math.floor(mins / 60);
        if (hours > 0) return \`\${hours}h \${mins % 60}m left\`;
        return \`\${mins}m left\`;
    }

    // \u2500\u2500 API Synchronization \u2500\u2500
    async function syncAccounts(silent = false) {
        try {
            if (!silent) state.isLoading = true;
            const res = await fetch(\`\${API_BASE}/auth/router/status\`);
            if (!res.ok) throw new Error(\`HTTP \${res.status}\`);
            const data = await res.json();

            state.authenticated = !!data.authenticated;
            state.user = data.user || null;
            let prov = (data.active_provider || 'connector').toLowerCase();
            if (prov === 'google') prov = 'connector';
            state.activeProvider = prov;
            state.providers = data.providers || {};
            state.accounts = data.accounts || [];
            state.totalAccounts = data.total_accounts || state.accounts.length;
            state.maxAccounts = data.max_accounts || 50;
            state.activeAccountId = data.active_account_id || '';
            state.activeEmail = data.active_email || 'None';
            state.rotationMode = data.rotation_mode || 'failover';
            state.healthyCount = data.healthy_count || state.accounts.filter(a => a.status !== 'cooldown' && a.status !== 'error').length;
            state.cooldownCount = data.cooldown_count || state.accounts.filter(a => a.status === 'cooldown').length;

            updateAuthUI();
            updateProviderView(state.activeProvider);
            updateStatsUI();
            renderAccountsList();
        } catch (err) {
            console.error('Failed to sync router state:', err);
            if (!silent) showToast(\`Network error: \${err.message}\`, 'error');
            if (els.systemStatusText) {
                els.systemStatusText.textContent = 'MATRIX OFFLINE // RETRYING';
                els.systemStatusText.parentElement.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                els.systemStatusText.style.color = '#f87171';
            }
        } finally {
            state.isLoading = false;
        }
    }

    // \u2500\u2500 Update Auth UI \u2500\u2500
    function updateAuthUI() {
        if (!state.authenticated) {
            // Show lock overlay
            if (els.gateLock) els.gateLock.classList.remove('hidden');
            if (els.btnHeaderConnect) els.btnHeaderConnect.style.display = 'flex';
            if (els.userBadge) els.userBadge.style.display = 'none';

            if (els.systemStatusText) {
                els.systemStatusText.textContent = 'ROUTER LOCKED // AUTH REQUIRED';
                els.systemStatusText.parentElement.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                els.systemStatusText.style.color = '#f87171';
            }
        } else {
            // Authenticated: hide lock overlay
            if (els.gateLock) els.gateLock.classList.add('hidden');
            if (els.btnHeaderConnect) els.btnHeaderConnect.style.display = 'none';
            if (els.userBadge) {
                els.userBadge.style.display = 'flex';
                const username = state.user?.username || state.user?.email?.split('@')[0] || 'operator';
                const tier = state.user?.tier ? \` [\${state.user.tier.toUpperCase()}]\` : '';
                if (els.userName) els.userName.textContent = \`@\${username}\${tier}\`;
            }

            if (els.systemStatusText) {
                els.systemStatusText.textContent = \`MATRIX ONLINE // :\${window.location.port || '9099'}\`;
                els.systemStatusText.parentElement.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                els.systemStatusText.style.color = '#10b981';
            }
        }
    }

    // \u2500\u2500 Update Provider View Switcher \u2500\u2500
    function updateProviderView(provId) {
        document.querySelectorAll('.provider-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-provider') === provId);
        });

        // Hide all views first
        if (els.viewConnector) els.viewConnector.classList.toggle('hidden', provId !== 'connector');
        if (els.viewOllama) els.viewOllama.classList.toggle('hidden', provId !== 'ollama');
        if (els.view9Router) els.view9Router.classList.toggle('hidden', provId !== '9router');

        let title = '\u26A1 SOVEREIGN CONNECTOR';
        let footerText = 'Sovereign Connector (Google Pool)';
        if (provId === 'ollama') {
            title = '\uD83E\uDD99 OLLAMA LOCAL ENGINE';
            footerText = 'Ollama Local Engine (Offline GPU)';
        } else if (provId === '9router') {
            title = '\uD83D\uDD00 9ROUTER GATEWAY';
            footerText = '9Router Universal Proxy';
        }

        if (els.currentProviderTag) els.currentProviderTag.textContent = title;
        if (els.footerActiveProvider) els.footerActiveProvider.textContent = footerText;

        // Populate provider forms with stored config
        if (provId === 'ollama') {
            const oCfg = state.providers?.ollama || {};
            if (els.inputOllamaHost && oCfg.host) els.inputOllamaHost.value = oCfg.host;
            if (els.inputOllamaModel && oCfg.default_model) els.inputOllamaModel.value = oCfg.default_model;
            renderOllamaModelChips();
        } else if (provId === '9router') {
            const rCfg = state.providers?.['9router'] || {};
            if (els.input9RouterHost && rCfg.host) els.input9RouterHost.value = rCfg.host;
            if (els.input9RouterKey && rCfg.api_key) els.input9RouterKey.value = rCfg.api_key;
            if (els.input9RouterModel && rCfg.default_model) els.input9RouterModel.value = rCfg.default_model;
            render9RouterModelChips();
        }
    }

    async function switchActiveProvider(provId) {
        try {
            state.activeProvider = provId;
            updateProviderView(provId);

            const res = await fetch(\`\${API_BASE}/auth/router/provider-config\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active_provider: provId })
            });
            const data = await res.json();
            if (data.success) {
                showToast(\`Switched active inference engine to: \${provId.toUpperCase()}\`, 'success');
            }
        } catch (err) {
            showToast(\`Provider switch error: \${err.message}\`, 'error');
        }
    }

    // \u2500\u2500 Ollama Preset Model Management \u2500\u2500
    function renderOllamaModelChips() {
        if (!els.ollamaModelsChips) return;
        const oCfg = state.providers?.ollama || {};
        let models = Array.isArray(oCfg.custom_models) ? oCfg.custom_models : ['deepseek-v4-9b-uncensored:latest', 'qwen2.5-coder:7b', 'qwen2.5-coder:1.5b'];
        const currentActive = (els.inputOllamaModel?.value?.trim() || oCfg.default_model || '').toLowerCase();

        els.ollamaModelsChips.innerHTML = models.map(m => {
            const isActive = m.toLowerCase() === currentActive;
            return \`
                <div class="model-chip \${isActive ? 'active' : ''}" data-model="\${escapeHtml(m)}">
                    <span class="chip-name">\${escapeHtml(m)}</span>
                    <span class="chip-remove" data-remove-model="\${escapeHtml(m)}" title="Hapus model dari preset">\u2715</span>
                </div>
            \`;
        }).join('');

        els.ollamaModelsChips.querySelectorAll('.chip-name').forEach(span => {
            span.addEventListener('click', () => {
                const parent = span.closest('.model-chip');
                const model = parent.getAttribute('data-model');
                if (els.inputOllamaModel) {
                    els.inputOllamaModel.value = model;
                    renderOllamaModelChips();
                }
            });
        });

        els.ollamaModelsChips.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const m = btn.getAttribute('data-remove-model');
                removeOllamaModelPreset(m);
            });
        });
    }

    function removeOllamaModelPreset(modelName) {
        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['deepseek-v4-9b-uncensored:latest', 'qwen2.5-coder:7b', 'qwen2.5-coder:1.5b'];
        state.providers.ollama.custom_models = models.filter(m => m !== modelName);
        renderOllamaModelChips();
        saveOllama(true);
        showToast(\`Model "\${modelName}" dihapus dari preset.\`, 'info');
    }

    function addOllamaModelPreset() {
        const val = els.inputOllamaModel?.value?.trim();
        if (!val) {
            showToast('Ketik nama model terlebih dahulu!', 'warning');
            els.inputOllamaModel?.focus();
            return;
        }
        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['deepseek-v4-9b-uncensored:latest', 'qwen2.5-coder:7b', 'qwen2.5-coder:1.5b'];
        if (!models.includes(val)) {
            models.push(val);
            state.providers.ollama.custom_models = models;
            renderOllamaModelChips();
            saveOllama(true);
            showToast(\`Model "\${val}" berhasil ditambahkan ke preset!\`, 'success');
        } else {
            showToast(\`Model "\${val}" sudah ada di preset.\`, 'info');
        }
    }

    // \u2500\u2500 9Router Preset Model Management \u2500\u2500
    function render9RouterModelChips() {
        if (!els.r9ModelsChips) return;
        const rCfg = state.providers?.['9router'] || {};
        let models = Array.isArray(rCfg.custom_models) ? rCfg.custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        const currentActive = (els.input9RouterModel?.value?.trim() || rCfg.default_model || '').toLowerCase();

        els.r9ModelsChips.innerHTML = models.map(m => {
            const isActive = m.toLowerCase() === currentActive;
            return \`
                <div class="model-chip \${isActive ? 'active' : ''}" data-model="\${escapeHtml(m)}">
                    <span class="chip-name">\${escapeHtml(m)}</span>
                    <span class="chip-remove" data-remove-model="\${escapeHtml(m)}" title="Hapus model dari preset">\u2715</span>
                </div>
            \`;
        }).join('');

        els.r9ModelsChips.querySelectorAll('.chip-name').forEach(span => {
            span.addEventListener('click', () => {
                const parent = span.closest('.model-chip');
                const model = parent.getAttribute('data-model');
                if (els.input9RouterModel) {
                    els.input9RouterModel.value = model;
                    render9RouterModelChips();
                }
            });
        });

        els.r9ModelsChips.querySelectorAll('.chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const m = btn.getAttribute('data-remove-model');
                remove9RouterModelPreset(m);
            });
        });
    }

    function remove9RouterModelPreset(modelName) {
        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        state.providers['9router'].custom_models = models.filter(m => m !== modelName);
        render9RouterModelChips();
        save9Router(true);
        showToast(\`Model "\${modelName}" dihapus dari preset.\`, 'info');
    }

    function add9RouterModelPreset() {
        const val = els.input9RouterModel?.value?.trim();
        if (!val) {
            showToast('Ketik nama model terlebih dahulu!', 'warning');
            els.input9RouterModel?.focus();
            return;
        }
        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        if (!models.includes(val)) {
            models.push(val);
            state.providers['9router'].custom_models = models;
            render9RouterModelChips();
            save9Router(true);
            showToast(\`Model "\${val}" berhasil ditambahkan ke preset!\`, 'success');
        } else {
            showToast(\`Model "\${val}" sudah ada di preset.\`, 'info');
        }
    }

    // \u2500\u2500 Test & Save Ollama \u2500\u2500
    async function testOllama() {
        const host = els.inputOllamaHost?.value?.trim() || 'http://127.0.0.1:11434';
        if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = 'Pinging...';
        if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill';

        try {
            const res = await fetch(\`\${API_BASE}/auth/router/test-provider\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: 'ollama', host })
            });
            const data = await res.json();

            if (data.success && data.online) {
                if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = \`Online (\${data.count} models)\`;
                if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill online';
                showToast(\`Ollama is Online at \${host}! Ditemukan \${data.count} model.\`, 'success');

                // Merge detected models
                if (Array.isArray(data.models) && data.models.length > 0) {
                    if (!state.providers.ollama) state.providers.ollama = {};
                    let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : [];
                    data.models.forEach(m => {
                        if (!models.includes(m)) models.push(m);
                    });
                    state.providers.ollama.custom_models = models;
                    if (!els.inputOllamaModel?.value?.trim()) {
                        els.inputOllamaModel.value = data.models[0];
                    }
                    renderOllamaModelChips();
                    saveOllama(true);
                }
            } else {
                if (els.ollamaPingTxt) els.ollamaPingTxt.textContent = 'Offline';
                if (els.ollamaPingPill) els.ollamaPingPill.className = 'panel-status-pill offline';
                showToast(\`Ollama unreachable at \${host}: \${data.error || 'Connection failed'}\`, 'error');
            }
        } catch (err) {
            showToast(\`Ollama test error: \${err.message}\`, 'error');
        }
    }

    async function saveOllama(silent = false) {
        const host = els.inputOllamaHost?.value?.trim() || 'http://127.0.0.1:11434';
        const default_model = els.inputOllamaModel?.value?.trim() || 'deepseek-v4-9b-uncensored:latest';

        if (!state.providers.ollama) state.providers.ollama = {};
        let models = Array.isArray(state.providers.ollama.custom_models) ? state.providers.ollama.custom_models : ['deepseek-v4-9b-uncensored:latest', 'qwen2.5-coder:7b', 'qwen2.5-coder:1.5b'];
        if (default_model && !models.includes(default_model)) {
            models.push(default_model);
        }
        state.providers.ollama.host = host;
        state.providers.ollama.default_model = default_model;
        state.providers.ollama.custom_models = models;

        try {
            const res = await fetch(\`\${API_BASE}/auth/router/provider-config\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_provider: 'ollama',
                    ollama: { host, default_model, custom_models: models }
                })
            });
            const data = await res.json();
            if (data.success) {
                renderOllamaModelChips();
                if (!silent) showToast(\`Ollama tersimpan! Model Aktif: \${default_model}\`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            if (!silent) showToast(\`Save error: \${err.message}\`, 'error');
        }
    }

    // \u2500\u2500 Test & Save 9Router \u2500\u2500
    async function test9Router() {
        const host = els.input9RouterHost?.value?.trim() || 'http://127.0.0.1:20128';
        const api_key = els.input9RouterKey?.value?.trim() || '';

        if (els.r9PingTxt) els.r9PingTxt.textContent = 'Pinging...';
        if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill';

        try {
            const res = await fetch(\`\${API_BASE}/auth/router/test-provider\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: '9router', host, api_key })
            });
            const data = await res.json();

            if (data.success && data.online) {
                if (els.r9PingTxt) els.r9PingTxt.textContent = \`Online (\${data.count} models)\`;
                if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill online';
                showToast(\`9Router is Online! Ditemukan \${data.count} model.\`, 'success');

                if (Array.isArray(data.models) && data.models.length > 0) {
                    if (!state.providers['9router']) state.providers['9router'] = {};
                    let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : [];
                    data.models.forEach(m => {
                        if (!models.includes(m)) models.push(m);
                    });
                    state.providers['9router'].custom_models = models;
                    if (!els.input9RouterModel?.value?.trim()) {
                        els.input9RouterModel.value = data.models[0];
                    }
                    render9RouterModelChips();
                    save9Router(true);
                }
            } else {
                if (els.r9PingTxt) els.r9PingTxt.textContent = 'Offline';
                if (els.r9PingPill) els.r9PingPill.className = 'panel-status-pill offline';
                showToast(\`9Router unreachable at \${host}: \${data.error || 'Connection failed'}\`, 'error');
            }
        } catch (err) {
            showToast(\`9Router test error: \${err.message}\`, 'error');
        }
    }

    async function save9Router(silent = false) {
        const host = els.input9RouterHost?.value?.trim() || 'http://127.0.0.1:20128';
        const api_key = els.input9RouterKey?.value?.trim() || '';
        const default_model = els.input9RouterModel?.value?.trim() || 'clinepass/cline-pass/glm-5.2';

        if (!state.providers['9router']) state.providers['9router'] = {};
        let models = Array.isArray(state.providers['9router'].custom_models) ? state.providers['9router'].custom_models : ['clinepass/cline-pass/glm-5.2', 'deepseek/deepseek-r1', 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet'];
        if (default_model && !models.includes(default_model)) {
            models.push(default_model);
        }
        state.providers['9router'].host = host;
        state.providers['9router'].api_key = api_key;
        state.providers['9router'].default_model = default_model;
        state.providers['9router'].custom_models = models;

        try {
            const res = await fetch(\`\${API_BASE}/auth/router/provider-config\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_provider: '9router',
                    '9router': { host, api_key, default_model, custom_models: models }
                })
            });
            const data = await res.json();
            if (data.success) {
                render9RouterModelChips();
                if (!silent) showToast(\`9Router tersimpan! Model Aktif: \${default_model}\`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            if (!silent) showToast(\`Save error: \${err.message}\`, 'error');
        }
    }

    // \u2500\u2500 Update Metric Numbers & Badges \u2500\u2500
    function updateStatsUI() {
        if (els.statTotal) els.statTotal.textContent = state.totalAccounts;
        if (els.statMax) els.statMax.textContent = \`/ \${state.maxAccounts} max\`;
        if (els.statActiveEmail) {
            els.statActiveEmail.textContent = state.activeEmail;
            els.statActiveEmail.title = state.activeEmail;
        }
        if (els.statHealth) els.statHealth.textContent = \`\${state.healthyCount} Ready\`;
        if (els.statCooldownSub) {
            els.statCooldownSub.textContent = state.cooldownCount > 0 ? \`\${state.cooldownCount} in cooldown\` : '0 cooldown';
            els.statCooldownSub.style.color = state.cooldownCount > 0 ? '#f87171' : 'var(--text-muted)';
        }
        if (els.strategySelect) {
            els.strategySelect.value = state.rotationMode;
        }

        // Filter Counts
        const activeCount = state.accounts.filter(a => a.is_active || a.id === state.activeAccountId).length;
        if (els.tabAll) els.tabAll.textContent = state.totalAccounts;
        if (els.tabActive) els.tabActive.textContent = activeCount;
        if (els.tabReady) els.tabReady.textContent = state.healthyCount;
        if (els.tabCooldown) els.tabCooldown.textContent = state.cooldownCount;
    }

    // \u2500\u2500 Render Accounts List \u2500\u2500
    function renderAccountsList() {
        if (!els.accountsList) return;

        let filtered = [...state.accounts];
        const now = Date.now();

        if (state.filter === 'active') {
            filtered = filtered.filter(a => a.is_active || a.id === state.activeAccountId);
        } else if (state.filter === 'ready') {
            filtered = filtered.filter(a => !(a.is_active || a.id === state.activeAccountId) && a.status !== 'cooldown');
        } else if (state.filter === 'cooldown') {
            filtered = filtered.filter(a => a.status === 'cooldown' || (a.cooldown_until && a.cooldown_until > now));
        }

        if (state.searchQuery) {
            const q = state.searchQuery.toLowerCase();
            filtered = filtered.filter(a => (a.email && a.email.toLowerCase().includes(q)) || (a.name && a.name.toLowerCase().includes(q)));
        }

        if (filtered.length === 0) {
            if (state.accounts.length === 0) {
                els.accountsList.innerHTML = \`
                    <div class="empty-state">
                        <div class="empty-icon">\u2601\uFE0F</div>
                        <h3>No Accounts in Local Pool</h3>
                        <p>Click <strong>Unduh Akun (Sync Cloud)</strong> to restore accounts from your Cloud Vault, or click <strong>Add Google Account</strong>.</p>
                    </div>
                \`;
            } else {
                els.accountsList.innerHTML = \`
                    <div class="empty-state">
                        <div class="empty-icon">\uD83D\uDD0D</div>
                        <h3>No Matching Accounts</h3>
                        <p>No accounts found matching filter "\${state.filter}" or search query.</p>
                    </div>
                \`;
            }
            return;
        }

        els.accountsList.innerHTML = filtered.map((acc, idx) => {
            const isActive = acc.is_active || acc.id === state.activeAccountId;
            const isCooldown = acc.status === 'cooldown' || (acc.cooldown_until && acc.cooldown_until > now);
            const remainingSec = isCooldown ? (acc.cooldown_remaining_sec || Math.max(1, Math.ceil((acc.cooldown_until - now) / 1000))) : 0;

            let badgeHtml = '';
            if (isActive) {
                badgeHtml = \`<span class="acc-badge badge-active">ACTIVE PRIMARY</span>\`;
            } else if (isCooldown) {
                badgeHtml = \`<span class="acc-badge badge-limit" data-cd-id="\${acc.id}">LIMIT 429 (\${remainingSec}s)</span>\`;
            } else {
                badgeHtml = \`<span class="acc-badge badge-ready">READY</span>\`;
            }

            const email = acc.email || 'unknown@google.com';
            const initial = (acc.name || email).charAt(0).toUpperCase();
            const requests = acc.requests_count || 0;
            const errors = acc.errors_count || 0;
            const expires = formatTimeRemaining(acc.expires_at);

            return \`
                <div class="account-card \${isActive ? 'is-active' : ''} \${isCooldown ? 'is-cooldown' : ''}">
                    <div class="acc-left">
                        <span class="acc-index">#\${idx + 1}</span>
                        <div class="acc-avatar">\${initial}</div>
                        <div class="acc-info">
                            <div class="acc-email-row">
                                <span class="acc-email" title="\${escapeHtml(email)}">\${escapeHtml(email)}</span>
                                \${badgeHtml}
                            </div>
                            <div class="acc-meta">
                                <div class="acc-meta-item">Requests: <span>\${requests}</span></div>
                                <div class="acc-meta-item">Errors: <span>\${errors}</span></div>
                                <div class="acc-meta-item">Token: <span>\${expires}</span></div>
                            </div>
                        </div>
                    </div>
                    <div class="acc-right">
                        \${isActive ? \`
                            <button class="btn-card btn-card-active" disabled>Primary</button>
                        \` : \`
                            <button class="btn-card btn-card-select" data-action="select" data-id="\${acc.id}" data-email="\${escapeHtml(email)}">Set Active</button>
                        \`}
                        <button class="btn-card btn-card-test" data-action="test" data-id="\${acc.id}" data-email="\${escapeHtml(email)}">Test Token</button>
                        <button class="btn-card-delete" data-action="delete" data-id="\${acc.id}" data-email="\${escapeHtml(email)}" title="Delete Account">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
            \`;
        }).join('');

        // Wire Action Buttons
        els.accountsList.querySelectorAll('[data-action="select"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                btn.disabled = true;
                btn.textContent = 'Switching...';
                await selectAccount(id, email);
            });
        });

        els.accountsList.querySelectorAll('[data-action="test"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                btn.disabled = true;
                btn.textContent = 'Testing...';
                await testAccount(id, email, btn);
            });
        });

        els.accountsList.querySelectorAll('[data-action="delete"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const email = btn.getAttribute('data-email');
                await deleteAccount(id, email);
            });
        });
    }

    // \u2500\u2500 Flowork OS Login via auth.floworkos.com \u2500\u2500
    async function startFloworkLogin() {
        try {
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Connecting to auth.floworkos.com portal...';
            showToast('Opening auth.floworkos.com login portal...', 'info');

            const res = await fetch(\`\${API_BASE}/auth/login-url\`);
            const data = await res.json();

            if (data.gate_url) {
                window.open(data.gate_url, '_blank');
                if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Awaiting authorization in browser window...';

                if (state.authPolling) clearInterval(state.authPolling);
                let pollCount = 0;

                state.authPolling = setInterval(async () => {
                    pollCount++;
                    await syncAccounts(true);
                    if (state.authenticated) {
                        clearInterval(state.authPolling);
                        state.authPolling = null;
                        showToast(\`\uD83C\uDF89 Sovereign Gate Unlocked! Welcome @\${state.user?.username || 'operator'}\`, 'success');
                    } else if (pollCount > 90) {
                        clearInterval(state.authPolling);
                        state.authPolling = null;
                        if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Authorization session timed out. Click to retry.';
                    }
                }, 1500);
            }
        } catch (err) {
            showToast(\`Auth error: \${err.message}\`, 'error');
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = \`Error: \${err.message}\`;
        }
    }

    // \u2500\u2500 Submit Flowork Token Manually \u2500\u2500
    async function submitManualToken() {
        const token = (els.inputManualToken?.value || '').trim();
        if (!token) {
            showToast('Please paste a valid session token', 'error');
            return;
        }

        try {
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = 'Verifying token with auth.floworkos.com...';
            const res = await fetch(\`\${API_BASE}/auth/set-token\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            const data = await res.json();

            if (data.success) {
                showToast(\`Token verified! Loaded \${data.cloud_accounts || 0} Cloud Vault accounts.\`, 'success');
                if (els.inputManualToken) els.inputManualToken.value = '';
                await syncAccounts();
            } else {
                showToast(data.error || 'Token verification failed', 'error');
                if (els.lockStatusTxt) els.lockStatusTxt.textContent = \`Error: \${data.error || 'Invalid token'}\`;
            }
        } catch (err) {
            showToast(\`Submit error: \${err.message}\`, 'error');
            if (els.lockStatusTxt) els.lockStatusTxt.textContent = \`Error: \${err.message}\`;
        }
    }

    // \u2500\u2500 Download Accounts from Cloud Vault \u2500\u2500
    async function syncCloudVault() {
        if (!state.authenticated) {
            showToast('Connect to Flowork OS first to sync Cloud Vault', 'error');
            return;
        }

        try {
            showToast('\u2601\uFE0F Downloading accounts from auth.floworkos.com Cloud Vault...', 'info');
            if (els.btnSyncCloud) {
                els.btnSyncCloud.disabled = true;
                els.btnSyncCloud.querySelector('span:last-child').textContent = 'Downloading...';
            }

            const res = await fetch(\`\${API_BASE}/auth/router/sync-cloud\`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                showToast(\`\u2601\uFE0F Cloud Vault Synced: \${data.count} accounts downloaded!\`, 'success');
                await syncAccounts();
            } else {
                showToast(\`Cloud Sync failed: \${data.error || 'Unknown error'}\`, 'error');
            }
        } catch (err) {
            showToast(\`Cloud Sync error: \${err.message}\`, 'error');
        } finally {
            if (els.btnSyncCloud) {
                els.btnSyncCloud.disabled = false;
                els.btnSyncCloud.querySelector('span:last-child').textContent = 'Unduh Akun (Sync Cloud)';
            }
        }
    }

    // \u2500\u2500 Sign Out \u2500\u2500
    async function logout() {
        if (!confirm('Are you sure you want to sign out from auth.floworkos.com? The router will be locked.')) return;
        try {
            const res = await fetch(\`\${API_BASE}/auth/logout\`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Signed out. Sovereign Router locked.', 'info');
                await syncAccounts();
            }
        } catch (err) {
            showToast(\`Logout error: \${err.message}\`, 'error');
        }
    }

    // \u2500\u2500 Account Management Actions \u2500\u2500
    async function addGoogleAccount() {
        if (!state.authenticated) {
            showToast('Please connect to Flowork OS first', 'error');
            return;
        }

        try {
            showToast('Opening Google OAuth in browser...', 'info');
            const res = await fetch(\`\${API_BASE}/auth/router/login-url?open=1\`);
            const data = await res.json();

            if (!data.success || !data.loginUrl) {
                throw new Error(data.error || 'Failed to get authorization URL');
            }

            window.open(data.loginUrl, '_blank');

            if (state.oauthPolling) clearInterval(state.oauthPolling);
            const initialCount = state.totalAccounts;
            let pollTicks = 0;

            state.oauthPolling = setInterval(async () => {
                pollTicks++;
                await syncAccounts(true);
                if (state.totalAccounts > initialCount) {
                    clearInterval(state.oauthPolling);
                    state.oauthPolling = null;
                    showToast('\uD83C\uDF89 New Google account linked to matrix pool!', 'success');
                } else if (pollTicks > 60) {
                    clearInterval(state.oauthPolling);
                    state.oauthPolling = null;
                }
            }, 2000);
        } catch (err) {
            showToast(\`OAuth Error: \${err.message}\`, 'error');
        }
    }

    async function selectAccount(id, email) {
        try {
            const res = await fetch(\`\${API_BASE}/auth/router/select-account\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(\`Switched active primary to: \${email}\`, 'success');
                await syncAccounts(true);
            } else {
                showToast(data.error || 'Failed to switch account', 'error');
            }
        } catch (err) {
            showToast(\`Error: \${err.message}\`, 'error');
        }
    }

    async function testAccount(id, email, btn) {
        try {
            const res = await fetch(\`\${API_BASE}/auth/router/test-account\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(\`\u26A1 Account \${email}: Token valid & active!\`, 'success');
            } else {
                showToast(\`\u26A0\uFE0F Account \${email}: \${data.error || 'Token check required'}\`, 'error');
            }
            await syncAccounts(true);
        } catch (err) {
            showToast(\`Test error: \${err.message}\`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Test Token';
            }
        }
    }

    async function deleteAccount(id, email) {
        if (!confirm(\`Are you sure you want to remove \${email} from the rotator pool?\`)) return;
        try {
            const res = await fetch(\`\${API_BASE}/auth/router/remove-account\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await res.json();
            if (data.success) {
                showToast(\`Removed \${email} from pool\`, 'info');
                await syncAccounts(true);
            } else {
                showToast(data.error || 'Failed to remove account', 'error');
            }
        } catch (err) {
            showToast(\`Delete error: \${err.message}\`, 'error');
        }
    }

    async function clearAllCooldowns() {
        try {
            const res = await fetch(\`\${API_BASE}/auth/router/clear-cooldown\`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast(\`Cleared cooldowns for \${data.cleared_count || 0} accounts\`, 'success');
                await syncAccounts(true);
            }
        } catch (err) {
            showToast(\`Failed: \${err.message}\`, 'error');
        }
    }

    async function setRotationMode(mode) {
        try {
            const res = await fetch(\`\${API_BASE}/auth/router/set-rotation-mode\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            const data = await res.json();
            if (data.success) {
                state.rotationMode = mode;
                showToast(\`Rotation strategy set to: \${mode}\`, 'info');
            }
        } catch (err) {
            showToast(\`Strategy error: \${err.message}\`, 'error');
        }
    }

    // \u2500\u2500 Setup Event Listeners \u2500\u2500
    function initEvents() {
        // Connect to Flowork OS buttons
        if (els.btnLockLogin) els.btnLockLogin.addEventListener('click', startFloworkLogin);
        if (els.btnHeaderConnect) els.btnHeaderConnect.addEventListener('click', startFloworkLogin);

        // Manual token
        if (els.btnSubmitToken) els.btnSubmitToken.addEventListener('click', submitManualToken);
        if (els.inputManualToken) {
            els.inputManualToken.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') submitManualToken();
            });
        }
        if (els.btnLogout) els.btnLogout.addEventListener('click', logout);

        // Provider Switcher Tabs
        document.querySelectorAll('.provider-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const provId = tab.getAttribute('data-provider');
                if (provId) switchActiveProvider(provId);
            });
        });

        // Ollama panel actions
        if (els.btnTestOllama) els.btnTestOllama.addEventListener('click', testOllama);
        if (els.btnSaveOllama) els.btnSaveOllama.addEventListener('click', () => saveOllama(false));
        if (els.btnAddOllamaModel) els.btnAddOllamaModel.addEventListener('click', addOllamaModelPreset);
        if (els.inputOllamaModel) {
            els.inputOllamaModel.addEventListener('input', () => {
                renderOllamaModelChips();
            });
            els.inputOllamaModel.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    addOllamaModelPreset();
                }
            });
        }

        // 9Router panel actions
        if (els.btnTest9Router) els.btnTest9Router.addEventListener('click', test9Router);
        if (els.btnSave9Router) els.btnSave9Router.addEventListener('click', () => save9Router(false));
        if (els.btnAdd9RouterModel) els.btnAdd9RouterModel.addEventListener('click', add9RouterModelPreset);
        if (els.input9RouterModel) {
            els.input9RouterModel.addEventListener('input', () => {
                render9RouterModelChips();
            });
            els.input9RouterModel.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    add9RouterModelPreset();
                }
            });
        }

        // Toolbar actions
        if (els.btnSyncCloud) els.btnSyncCloud.addEventListener('click', syncCloudVault);
        if (els.btnAddAccount) els.btnAddAccount.addEventListener('click', addGoogleAccount);
        if (els.btnRefreshPool) {
            els.btnRefreshPool.addEventListener('click', () => {
                showToast('Refreshing pool status...', 'info');
                syncAccounts();
            });
        }
        if (els.btnClearCooldown) els.btnClearCooldown.addEventListener('click', clearAllCooldowns);

        if (els.strategySelect) {
            els.strategySelect.addEventListener('change', (e) => {
                setRotationMode(e.target.value);
            });
        }

        // Filter Tabs
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                state.filter = tab.getAttribute('data-filter') || 'all';
                renderAccountsList();
            });
        });

        // Search Input
        if (els.searchInput) {
            els.searchInput.addEventListener('input', (e) => {
                state.searchQuery = e.target.value.trim();
                if (els.searchClearBtn) {
                    els.searchClearBtn.classList.toggle('hidden', state.searchQuery.length === 0);
                }
                renderAccountsList();
            });
        }

        if (els.searchClearBtn) {
            els.searchClearBtn.addEventListener('click', () => {
                if (els.searchInput) els.searchInput.value = '';
                state.searchQuery = '';
                els.searchClearBtn.classList.add('hidden');
                renderAccountsList();
            });
        }

        // Live Cooldown Second-by-Second Countdown
        setInterval(() => {
            const now = Date.now();
            let hasChanged = false;
            document.querySelectorAll('[data-cd-id]').forEach(badge => {
                const id = badge.getAttribute('data-cd-id');
                const acc = state.accounts.find(a => a.id === id);
                if (acc && acc.cooldown_until) {
                    const remaining = Math.max(0, Math.ceil((acc.cooldown_until - now) / 1000));
                    if (remaining > 0) {
                        badge.textContent = \`LIMIT 429 (\${remaining}s)\`;
                    } else {
                        hasChanged = true;
                    }
                }
            });
            if (hasChanged) syncAccounts(true);
        }, 1000);

        // Periodic Background Sync (every 6s)
        setInterval(() => syncAccounts(true), 6000);
    }

    // Initialize
    initEvents();
    syncAccounts();
})();
`}});var Jt=L(()=>{var Un=g("http"),Vn=g("url"),on=g("path"),Kn=g("fs"),f=cn(),Wt=Fn(),Z=Zn(),Xt=U(),jn=R(),en=Dn(),P=parseInt(process.env.CONNECTOR_PORT||process.env.FLOWORK_ROUTER_PORT||jn.getSettings().port||9099,10),J=jn.getSettings().host||"127.0.0.1",fn=process.env.FLOWORK_GUI_DIR||on.join(Xt.baseDir,"gui");function qn(t){t.setHeader("Access-Control-Allow-Origin","*"),t.setHeader("Access-Control-Allow-Methods","GET, POST, PUT, DELETE, OPTIONS"),t.setHeader("Access-Control-Allow-Headers","Content-Type, Authorization, X-Requested-With, Origin, Accept")}function un(t,n,l,a){if(Kn.existsSync(n))Kn.readFile(n,(e,o)=>{if(!e)return t.writeHead(200,{"Content-Type":l}),t.end(o);if(a&&en[a])return t.writeHead(200,{"Content-Type":l}),t.end(en[a]);t.writeHead(404,{"Content-Type":"text/plain"}),t.end("File Not Found")});else if(a&&en[a])return t.writeHead(200,{"Content-Type":l}),t.end(en[a]);else t.writeHead(404,{"Content-Type":"text/plain"}),t.end("File Not Found")}async function nt(t,n,l){let a=l.query.token||l.query.flowork_token,e=String(l.query.state||""),o=l.query.code,r=l.query.error;if(a){let i=await f.verifyFloworkToken(a);if(i.valid){let d=f.loadVault();d.flowork_token=a,d.flowork_user=i.user,d.is_logged_out=!1,f.saveVault(d),console.log(`[Server] \u2705 Flowork OS Passport authenticated for @${i.user.username}`);let s=(await f.pullCloudVault(a)).count||0,p=`<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MrFlow \u2014 Authenticated</title>
    <style>
        body { margin:0; background:#070b14; color:#fff; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; }
        .card { background:#0f172a; border:1px solid #10b981; border-radius:18px; padding:36px 44px; text-align:center; max-width:440px; box-shadow:0 12px 36px rgba(0,0,0,0.8), 0 0 24px rgba(16,185,129,0.3); }
        .icon { font-size:44px; margin-bottom:12px; }
        h1 { font-size:22px; color:#10b981; margin:0 0 8px; }
        p { font-size:13.5px; color:#94a3b8; line-height:1.6; margin:0 0 20px; }
        .btn { background:#10b981; color:#fff; font-weight:700; border:none; padding:10px 24px; border-radius:999px; cursor:pointer; font-size:13px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">\uD83D\uDEE1\uFE0F</div>
        <h1>Welcome, @${i.user.username}!</h1>
        <p>Your session with <strong>auth.floworkos.com</strong> has been verified.<br>Cloud Vault successfully synchronized (<strong>${s}</strong> accounts loaded).</p>
        <button class="btn" onclick="window.close()">Close Window</button>
    </div>
    <script>setTimeout(() => window.close(), 1800);</script>
</body>
</html>`;return n.writeHead(200,{"Content-Type":"text/html; charset=utf-8"}),n.end(p)}else return n.writeHead(401,{"Content-Type":"text/html; charset=utf-8"}),n.end(`<h2>Authentication Failed</h2><p>${i.error}</p>`)}if(e.startsWith("flw_multi_")){if(r)return n.writeHead(200,{"Content-Type":"text/html; charset=utf-8"}),n.end('<h2>Google Authorization Cancelled</h2><button onclick="window.close()">Close</button>');let i=f.loadVault(),d=f.pendingPkceSessions.get(e)||i.pending_oauth_sessions?.[e],c=d?.verifier||"",s=d?.redirectUri||"http://localhost:8080/callback";if(f.pendingPkceSessions.delete(e),i.pending_oauth_sessions)delete i.pending_oauth_sessions[e];let p=await f.exchangeOAuthCode(o,c,s);if(!p.success||!p.tokens?.access_token)return n.writeHead(500,{"Content-Type":"text/html; charset=utf-8"}),n.end(`<h2>Token Exchange Failed</h2><p>${p.error}</p>`);let b=p.tokens,u=b.email||"",E="";if(!u&&b.id_token){let m=f.parseJwtClaims(b.id_token);if(m?.email)u=m.email;if(m?.name)E=m.name}if(!u){let m=await f.fetchGoogleUserInfo(b.access_token);if(m.success&&m.user?.email)u=m.user.email,E=m.user.name||""}if(!u)u=`account_${i.accounts.length+1}@gmail.com`;let w=i.accounts.find((m)=>m.email.toLowerCase()===u.toLowerCase());if(w){if(w.access_token=b.access_token,b.refresh_token)w.refresh_token=b.refresh_token;w.expires_at=Date.now()+(b.expires_in||3600)*1000,w.status="ready",w.cooldown_until=0,w.error_message=""}else{let m={id:"acc_"+Date.now().toString(36)+"_"+Math.random().toString(36).substring(2,6),email:u,name:E||u.split("@")[0],access_token:b.access_token,refresh_token:b.refresh_token||"",expires_at:Date.now()+(b.expires_in||3600)*1000,status:"ready",cooldown_until:0,requests_count:0,errors_count:0,added_at:new Date().toISOString(),last_used_at:new Date().toISOString(),error_message:""};if(i.accounts.push(m),!i.active_account_id)i.active_account_id=m.id}f.saveVault(i);let y={success:!1};try{y=await f.pushCloudVault(i),console.log(`[Server] \u2601\uFE0F Auto-backed up new account [${u}] to auth.floworkos.com:`,y.success?"Success":y.error)}catch(m){console.error("[Server] \u2601\uFE0F Cloud auto-backup error:",m.message)}return n.writeHead(200,{"Content-Type":"text/html; charset=utf-8"}),n.end(`<!DOCTYPE html><html><body style="background:#070b14;color:#fff;font-family:sans-serif;text-align:center;padding:40px;">
            <h1 style="color:#10b981;">Google Account Linked</h1>
            <p><strong>${u}</strong> has been added to the accounts pool.</p>
            <p style="color:#64748b;font-size:12px;">Cloud Vault Backup: ${y.success?"Synchronized":"Saved locally"}</p>
            <script>setTimeout(() => window.close(), 1800);</script>
        </body></html>`)}return n.writeHead(400,{"Content-Type":"text/plain"}),n.end("Invalid callback parameters")}var Zt=Un.createServer(async(t,n)=>{if(qn(n),t.method==="OPTIONS")return n.writeHead(204),n.end();let l=Vn.parse(t.url,!0),a=l.pathname;if(a==="/health")return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({status:"ok",online:!0}));if(a==="/"||a==="/gui"||a==="/gui/"||a==="/index.html")return un(n,on.join(fn,"index.html"),"text/html; charset=utf-8","indexHtml");if(a==="/gui/style.css"||a==="/style.css")return un(n,on.join(fn,"style.css"),"text/css; charset=utf-8","styleCss");if(a==="/gui/app.js"||a==="/app.js")return un(n,on.join(fn,"app.js"),"application/javascript; charset=utf-8","appJs");if(a==="/auth/router/accounts"||a==="/api/router/accounts"||a==="/auth/router/status"||a==="/api/router/status"||a==="/auth/router/refresh-pool"){let e=f.loadVault(),o=Date.now(),r=!!(e.flowork_token&&e.flowork_user);if(!e.providers)e.providers=JSON.parse(JSON.stringify(Z.DEFAULT_PROVIDERS)),f.saveVault(e);e.accounts.sort((p,b)=>{let u=p.cooldown_until&&p.cooldown_until>o?1:0,E=b.cooldown_until&&b.cooldown_until>o?1:0;return u-E});let i=e.accounts.map((p)=>{let b=p.cooldown_until&&p.cooldown_until>o;return{id:p.id,email:p.email,name:p.name||p.email.split("@")[0],status:b?"cooldown":p.status||"ready",cooldown_until:b?p.cooldown_until:0,cooldown_remaining_sec:b?Math.ceil((p.cooldown_until-o)/1000):0,is_active:p.id===e.active_account_id,expires_at:p.expires_at||0,requests_count:p.requests_count||0,errors_count:p.errors_count||0,added_at:p.added_at,last_used_at:p.last_used_at,error_message:p.error_message||""}}),d=i.find((p)=>p.is_active),c=i.filter((p)=>p.status!=="cooldown"&&p.status!=="error").length,s=i.filter((p)=>p.status==="cooldown").length;if(!e.providers)e.providers=JSON.parse(JSON.stringify(Z.DEFAULT_PROVIDERS));return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,connected:!0,authenticated:r,user:e.flowork_user||null,active_provider:e.active_provider||"connector",providers:e.providers,port:P,total_accounts:i.length,max_accounts:f.config.max_accounts||50,active_account_id:e.active_account_id||(i[0]?.id||""),active_email:d?d.email:i[0]?.email||"None",rotation_mode:e.rotation_mode||"failover",healthy_count:c,cooldown_count:s,accounts:i}))}if(a==="/auth/router/provider-config"||a==="/api/router/provider-config"){let e=f.loadVault();if(!e.providers)e.providers=JSON.parse(JSON.stringify(Z.DEFAULT_PROVIDERS));if(t.method==="GET")return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,active_provider:e.active_provider||"connector",providers:e.providers}));if(t.method==="POST"){let o="";t.on("data",(r)=>o+=r),t.on("end",()=>{try{let r=JSON.parse(o||"{}");if(r.active_provider)e.active_provider=r.active_provider,console.log(`[Server] Active AI Provider set to: ${r.active_provider}`);if(r.ollama){if(!e.providers.ollama)e.providers.ollama={};if(r.ollama.host)e.providers.ollama.host=r.ollama.host;if(r.ollama.default_model)e.providers.ollama.default_model=r.ollama.default_model;if(Array.isArray(r.ollama.custom_models))e.providers.ollama.custom_models=r.ollama.custom_models}let i=r["9router"]||r.router9;if(i){if(!e.providers["9router"])e.providers["9router"]={};if(i.host)e.providers["9router"].host=i.host;if(i.api_key!==void 0)e.providers["9router"].api_key=i.api_key;if(i.default_model)e.providers["9router"].default_model=i.default_model;if(Array.isArray(i.custom_models))e.providers["9router"].custom_models=i.custom_models}return f.saveVault(e),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,active_provider:e.active_provider,providers:e.providers}))}catch(r){return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:r.message}))}});return}}if(a==="/auth/router/test-provider"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",async()=>{try{let o=JSON.parse(e||"{}"),r=o.provider||"ollama";if(r==="ollama"){let i=o.host||"http://127.0.0.1:11434",d=await Z.testOllamaConnectivity(i);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify(d))}if(r==="9router"){let i=o.host||"http://127.0.0.1:20128",d=o.api_key||"",c=await Z.test9RouterConnectivity(i,d);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify(c))}n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Unknown provider: "+r}))}catch(o){n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/login-url"||a==="/auth/ticket"||a==="/api/auth/ticket"){let{ticket:e,gateUrl:o}=f.createSessionTicket(P);if(t.method==="GET"&&!l.query.no_open)f.openUrlInBrowser(o);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({status:"STARTED",ticket:e,gate_url:o,login_url:o,port:P}))}if(a==="/auth/callback"||a==="/callback"||a==="/auth/flowork-callback")return nt(t,n,l);if(a==="/auth/router/add-account"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",async()=>{try{let o=JSON.parse(e||"{}"),r=(o.email||"").trim(),i=(o.refresh_token||"").trim(),d=(o.access_token||"").trim(),c=(o.name||r.split("@")[0]).trim();if(!r)return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Email is required"}));if(!i&&!d)return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Refresh token or access token is required"}));let s=f.loadVault(),p=s.accounts.find((u)=>u.email.toLowerCase()===r.toLowerCase());if(p){if(i)p.refresh_token=i;if(d)p.access_token=d,p.expires_at=Date.now()+3600000;p.status="ready",p.cooldown_until=0,p.error_message=""}else{let u={id:"acc_"+Date.now().toString(36)+"_"+Math.random().toString(36).substring(2,6),email:r,name:c||r.split("@")[0],access_token:d,refresh_token:i,expires_at:d?Date.now()+3600000:0,status:"ready",cooldown_until:0,requests_count:0,errors_count:0,added_at:new Date().toISOString(),last_used_at:new Date().toISOString(),error_message:""};if(s.accounts.push(u),!s.active_account_id)s.active_account_id=u.id}f.saveVault(s);let b={success:!1,message:"Cloud backup skipped (no flowork token)"};if(s.flowork_token)b=await f.pushCloudVault(s),console.log(`[Server] \u2601\uFE0F Auto-backup account [${r}] to auth.floworkos.com:`,b.success?"Success":b.error);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,email:r,total_accounts:s.accounts.length,cloud_backup:b}))}catch(o){return n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/router/sync-cloud"||a==="/api/router/sync-cloud"){if(!f.loadVault().flowork_token)return n.writeHead(401,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Not authenticated with auth.floworkos.com. Please sign in first."}));try{let o=await f.pullCloudVault();if(o.success)return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,count:o.count,accounts:o.accounts,message:`Downloaded ${o.count} accounts from Cloud Vault`}));else return n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.error}))}catch(o){return n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}}if(a==="/auth/set-token"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",async()=>{try{let o=JSON.parse(e||"{}"),r=(o.token||o.flowork_token||"").trim();if(!r)return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Token missing"}));let i=await f.verifyFloworkToken(r);if(!i.valid)return n.writeHead(401,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:i.error||"Token invalid"}));let d=f.loadVault();d.flowork_token=r,d.flowork_user=i.user,d.is_logged_out=!1,f.saveVault(d);let c=await f.pullCloudVault(r);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,user:i.user,cloud_accounts:c.count||0}))}catch(o){return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/logout"&&t.method==="POST"){let e=f.loadVault();return e.flowork_token="",e.flowork_user=null,e.is_logged_out=!0,e.accounts=[],e.active_account_id="",f.saveVault(e),console.log("[Server] \uD83D\uDEAA Signed out from auth.floworkos.com. Router locked."),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,message:"Signed out successfully"}))}if(a==="/auth/router/login-url")try{let e=await f.generateLoginUrl(P);if(l.query?.open==="1")f.openUrlInBrowser(e.loginUrl);return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,provider:"google",loginUrl:e.loginUrl,state:e.state}))}catch(e){return n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:e.message}))}if(a==="/auth/router/select-account"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",()=>{try{let r=JSON.parse(e||"{}").id,i=f.loadVault(),d=i.accounts.find((c)=>c.id===r);if(!d)return n.writeHead(404,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Account not found"}));return i.active_account_id=r,f.saveVault(i),console.log(`[Server] Active account switched to: ${d.email}`),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,active_account_id:r,email:d.email}))}catch(o){return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/router/remove-account"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",()=>{try{let r=JSON.parse(e||"{}").id,i=f.loadVault(),d=i.accounts.length;if(i.accounts=i.accounts.filter((c)=>c.id!==r),i.accounts.length===d)return n.writeHead(404,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Account not found"}));if(i.active_account_id===r)i.active_account_id=i.accounts[0]?.id||"";return f.saveVault(i),f.pushCloudVault(i).catch(()=>{}),console.log(`[Server] Removed account ${r}. Remaining: ${i.accounts.length}`),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,remaining:i.accounts.length}))}catch(o){return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/router/set-rotation-mode"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",()=>{try{let r=JSON.parse(e||"{}").mode||"failover",i=f.loadVault();return i.rotation_mode=r,f.saveVault(i),f.pushCloudVault(i).catch(()=>{}),console.log(`[Server] Rotation mode set to: ${r}`),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,rotation_mode:r}))}catch(o){return n.writeHead(400,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/router/test-account"&&t.method==="POST"){let e="";t.on("data",(o)=>e+=o),t.on("end",async()=>{try{let r=JSON.parse(e||"{}").id,i=f.loadVault(),d=i.accounts.find((s)=>s.id===r);if(!d)return n.writeHead(404,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:"Account not found"}));let c=await f.refreshAccountToken(d,!0);return f.saveVault(i),n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:c.refreshed||!c.error,email:d.email,status:d.status,expires_at:d.expires_at,details:c}))}catch(o){return n.writeHead(500,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!1,error:o.message}))}});return}if(a==="/auth/router/clear-cooldown"&&t.method==="POST"){let e=f.clearAllCooldowns();return n.writeHead(200,{"Content-Type":"application/json"}),n.end(JSON.stringify({success:!0,cleared_count:e}))}return Wt.handleAiProxyRequest(t,n,l,a)});Zt.listen(P,J,()=>{console.log("======================================================="),console.log("\uD83D\uDE80 MrFlow Sovereign Connector & Account Rotator Online"),console.log(`\uD83D\uDCE1 Server Address: http://${J}:${P}`),console.log(`\uD83C\uDFA8 Web GUI:        http://${J}:${P}/gui`),console.log("======================================================="),f.startBackgroundTokenKeeper(60000)});function tt(t){let n=Un.createServer((l,a)=>{qn(a);let e=Vn.parse(l.url,!0),o=e.pathname;if(o==="/oauth-callback"||o==="/callback"||o==="/auth/callback")return nt(l,a,e);a.writeHead(404,{"Content-Type":"text/plain"}),a.end("Not Found")});return n.listen(t,J,()=>{console.log(`\uD83D\uDD17 Auxiliary Antigravity OAuth Callback: http://${J}:${t}/oauth-callback`)}),n.on("error",(l)=>{console.warn(`[Server] Auxiliary port ${t} note:`,l.message)}),n}var le=tt(51121),se=tt(8080)});export default Jt();
