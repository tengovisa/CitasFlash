#!/bin/bash
export SUPABASE_URL=https://wbtdoqrbavvzqwiqmgnu.supabase.co
export SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndidGRvcXJiYXZ2enF3aXFtZ251Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzU4NTg0OCwiZXhwIjoyMDg5MTYxODQ4fQ.INU4B41BDgJ21rtvmWkKPCdEKPKzsUB4Mtzw_Byhbbs
export API_KEY=CitaFast2026Bot2
export RESEND_API_KEY=re_3t41id3F_LoM2iy8EFNG76HnXTYxLRbu5
export VALIDATE_PROXY=http://axihbvupstaticresidential:ng8m7kbc1met@9.142.44.55:7724
cd /root && uvicorn api_control:app --host 0.0.0.0 --port 8000 --log-level warning
