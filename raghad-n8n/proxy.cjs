const http=require("node:http");
const {timingSafeEqual}=require("node:crypto");
const {spawn,spawnSync}=require("node:child_process");
const key=Buffer.from(process.env.RAGHAD_N8N_SHARED_KEY||"");
if(key.length<32)throw Error("Dispatch key is missing");
for(const args of [["import:workflow","--input=/opt/raghad/workflow.json"],["publish:workflow","--id=RaghadDispatchV1"]]){
 const result=spawnSync("n8n",args,{stdio:"inherit"});
 if(result.status!==0)process.exit(1);
}
const worker=spawn("n8n",["start"],{stdio:"inherit"});
worker.on("exit",code=>process.exit(code||0));
process.on("SIGTERM",()=>worker.kill("SIGTERM"));
const send=(res,status,body)=>res.writeHead(status,{"Content-Type":"application/json","Cache-Control":"no-store"}).end(body);
http.createServer(async(req,res)=>{
 try{
  if(req.method==="GET"&&req.url==="/healthz"){
   const result=await fetch("http://127.0.0.1:5678/healthz/readiness",{signal:AbortSignal.timeout(2000)});
   return send(res,result.ok?200:503,JSON.stringify({ok:result.ok}));
  }
  if(req.method!=="POST"||req.url!=="/dispatch")return send(res,404,'{"ok":false}');
  const supplied=Buffer.from(String(req.headers.authorization||"").replace(/^Bearer /,""));
  if(supplied.length!==key.length||!timingSafeEqual(supplied,key))return send(res,401,'{"ok":false}');
  let bytes=0;
  const chunks=[];
  for await(const chunk of req){bytes+=chunk.length;if(bytes>2048)return send(res,413,'{"ok":false}');chunks.push(chunk);}
  const body=JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const safe={jobId:body.jobId,approvalId:body.approvalId,branch:body.branch,format:body.format};
  const result=await fetch("http://127.0.0.1:5678/webhook/raghad-dispatch-v1",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(safe),signal:AbortSignal.timeout(8000)});
  return send(res,result.status,await result.text());
 }catch{return send(res,503,'{"ok":false}');}
}).listen(Number(process.env.PORT)||10000,"0.0.0.0");