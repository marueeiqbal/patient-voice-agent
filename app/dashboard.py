from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Patients Dashboard</title>
<style>
body{font-family:Arial,sans-serif;margin:24px;background:#f6f7f9}
h1{margin-top:0}
table{border-collapse:collapse;width:100%;background:#fff}
th,td{border:1px solid #ddd;padding:8px;font-size:14px;text-align:left}
th{background:#1f2937;color:#fff}
</style></head><body>
<h1>Registered Patients</h1>
<p id="count"></p>
<table><thead><tr>
<th>Name</th><th>DOB</th><th>Sex</th><th>Phone</th><th>Address</th><th>Insurance</th><th>Created (UTC)</th>
</tr></thead><tbody id="rows"></tbody></table>
<script>
fetch('/patients').then(r => r.json()).then(res => {
  const rows = document.getElementById('rows');
  const list = res.data || [];
  document.getElementById('count').textContent = list.length + ' patient(s)';
  list.forEach(p => {
    const tr = document.createElement('tr');
    const cells = [
      p.first_name + ' ' + p.last_name,
      p.date_of_birth, p.sex, p.phone_number,
      [p.address_line_1, p.address_line_2, p.city, p.state, p.zip_code].filter(Boolean).join(', '),
      p.insurance_provider || '-',
      p.created_at
    ];
    cells.forEach(c => { const td = document.createElement('td'); td.textContent = c; tr.appendChild(td); });
    rows.appendChild(tr);
  });
});
</script></body></html>"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return PAGE