const HOURS=24, DEMAND=10, CHARGE_CAP=40, TOTAL=240, BLOCKS=4, BLOCK_H=6;
function hourly(b){const p=[];for(let h=0;h<HOURS;h++)p.push(b[Math.floor(h/BLOCK_H)]);return p;}
function schedule(prices,storageMWh){
  const charge=new Array(HOURS).fill(0);
  function prof(){let soc=0;const end=new Array(HOURS);let d=-1;
    for(let h=0;h<HOURS;h++){soc+=charge[h]-DEMAND;end[h]=soc;if(soc<-1e-9&&d===-1)d=h;}
    return{end,deficit:d};}
  for(let it=0;it<4000;it++){
    const p=prof(); if(p.deficit===-1)break;
    const d=p.deficit, shortfall=-p.end[d];
    let best=-1,bp=Infinity,br=0;
    for(let j=0;j<=d;j++){
      const capRoom=CHARGE_CAP-charge[j]; if(capRoom<=1e-9)continue;
      let st=Infinity; for(let k=j;k<=d;k++) st=Math.min(st,storageMWh-p.end[k]);
      const room=Math.min(capRoom,st); if(room<=1e-9)continue;
      if(prices[j]<bp){bp=prices[j];best=j;br=room;}
    }
    if(best===-1){console.log("INFEASIBLE at deficit",d);break;}
    charge[best]+=Math.min(br,shortfall);
  }
  return charge;
}
function run(name,blocks,storeH){
  const prices=hourly(blocks), charge=schedule(prices,storeH*DEMAND);
  let flat=0,bat=0,tot=0;
  for(let h=0;h<HOURS;h++){flat+=DEMAND*prices[h];bat+=charge[h]*prices[h];tot+=charge[h];}
  console.log(`${name}  store=${storeH}h  totalBought=${tot.toFixed(1)} (want 240)  flat=$${(flat/TOTAL).toFixed(2)}  battery=$${(bat/TOTAL).toFixed(2)}  saving=${(100*(1-(bat/TOTAL)/(flat/TOTAL))).toFixed(0)}%`);
}
console.log("--- worked example: 30/45/0/110, expect flat $46.25, battery $15.00 ---");
run("solar   ",[30,45,0,110],12);
console.log("--- storage sweep ---");
[0,3,6,12,18].forEach(s=>run("solar   ",[30,45,0,110],s));
console.log("--- other presets ---");
[0,6,12,18].forEach(s=>run("mild    ",[30,45,25,70],s));
[0,6,12,18].forEach(s=>run("extreme ",[40,35,-15,140],s));
console.log("--- edge cases ---");
run("allsame ",[50,50,50,50],12);
run("negall  ",[-30,-30,-30,-30],12);
run("maxprice",[160,160,160,160],18);
