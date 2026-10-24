# API contract (the real backend must return these shapes; the mock already does)

All paths are under `/api`. Dates ISO (IST). Audit payload values are strings or ints (no floats).

| Method + path | Returns |
|---|---|
| POST /applications | 202 `{id, state}` |
| GET /applications/{id}/events | `{stages:[8 names], completed:int, done:bool}` (poll, or SSE in production) |
| GET /applications/{id}/summary | `{id, institution{name,state}, cycle, category, version, claims{...}, sampled, sampled_stale, anomaly{...}, overall: "READY_FOR_DECISION"\|"REVIEW_INCOMPLETE", open_checks:[ids], findings_open}` |
| GET /applications/{id}/coverage | `{requirements:[{id,title,doc,page,rung,required_rung,conflict,state,reason,coverage,waived?,by?}], checks:{id:state}, overall, open_checks:[...], waivers}` |
| GET /applications/{id}/claims | `{claims:[{key,value,bucket,prev,sampled}], counts:{UNCHANGED,CHANGED_WITH_EVIDENCE,CHANGED_NO_EXPLANATION,NEW}, sample:[keys]}` |
| GET /applications/{id}/diff | `{changed:[{key,from,to}], rules_rerun:[], findings_resolved:[], findings_pending:[], ribbon}` |
| GET /applications/{id}/timeline | `{today, semesters:[{name,start,end}], pins:[{doc,label,expires,inside_semester}]}` |
| GET /applications/{id}/photos | `{campus_polygon, photos:[{photo,status:"inside_campus"\|"far_from_campus"\|"no_location_data",km,lat,lon}]}` |
| GET /findings | `{findings:[{id,rule_id,rule_version,severity,state,req,claims,evidence:[{doc,page,box:[x0,y0,x1,y1],text}],explanation,next_step:{kind,cost,why},ai_read,decision,resolved,bundle_id}], bundles:[{id,root_cause,finding_ids,top_action,letter_en}]}` |
| GET /findings/{id}/graph | `{trace:[strings]}` |
| POST /findings/{id}/decision | body `{action:"accept"\|"dismiss"\|"request_info"}`; 422 if the finding is FAILED and action is accept/dismiss |
| POST /applications/{id}/resubmit | the diff object above |
| POST /applications/{id}/waivers | body `{check_id, reason}`; 403 unless role allowed and reason >= 15 chars |
| POST /applications/{id}/decision | body `{action:"approve"\|"reject"\|"request_info"}`; **409** `{detail, open_checks:[...]}` when approving with open unwaived checks |
| GET /documents/{id}/boxes, /file | boxes in PDF points, origin top-left (PyMuPDF); the PDF itself |
| GET /network/faculty/{token} | `{label, token, nodes:[{id,name}], edges:[{institution,from,to,kind}], overlaps:[{overlap_from,...}]}` |
| GET /alerts | `{alerts:[{id,kind,owner_role,due,status,ref}]}` |
| GET /rules | `{version, rules:[{id,title,inputs,params,severity,required_rung,clause}]}` |
| POST /rules/simulate | body `{rule_id,param,value}` -> `{count,total,first10}` |
| POST /replay | `{finding, rule, v1:{version,param,state}, v1_1:{...}}` |
| GET /audit, /audit/verify | chain rows `{seq,event:{ts,actor,event,payload},prev_hash,hash}`; `{intact,entries,first_broken_seq,head}` |
| GET /eval/summary | `{rows:[{id,what,expect_finding,found}], planted, found, false_positives}` |

Audit hash: `sha256(prev_hash + canonical_json(event))`, canonical = sorted keys, no spaces, UTF-8. Python and TypeScript produce identical hashes (golden-tested).
