function el(sel, text){ const e=document.createElement(sel); if(text)e.textContent=text; return e }

const flowEl = document.getElementById('flow')
const resultEl = document.getElementById('result')
const runBtn = document.getElementById('run')
const resetBtn = document.getElementById('reset')
const logArea = document.getElementById('logArea')
const copyLogs = document.getElementById('copyLogs')

function log(line){
  const t = new Date().toLocaleTimeString()
  logArea.textContent += `[${t}] ${line}\n`
  logArea.scrollTop = logArea.scrollHeight
}

function nodeHtml(label, meta){
  const n = el('div')
  n.className = 'node'
  n.innerHTML = `<strong>${label}</strong><span style="color:var(--muted);font-size:12px">${meta||''}</span>`
  return n
}

function renderMessage(side, text){
  const s = el('div')
  s.className = 'step msg flash'
  const left = nodeHtml(side, '')
  const arrow = el('div'); arrow.className='arrow'
  const right = el('div'); right.className='right'; right.textContent = text
  s.appendChild(left); s.appendChild(arrow); s.appendChild(right)
  flowEl.appendChild(s)
}

function clear(){ flowEl.innerHTML=''; resultEl.className=''; resultEl.textContent=''; logArea.textContent=''; }

function selectedClientVersions(){
  return Array.from(document.querySelectorAll('.ver:checked')).map(i=>i.value)
}

function selectedCiphers(){
  return Array.from(document.querySelectorAll('.cipher:checked')).map(i=>i.value)
}

function simulateSequence(){
  clear()
  const mode = document.getElementById('mode').value
  const attacker = document.getElementById('attacker').checked
  const speed = Number(document.getElementById('speed').value)
  const versions = selectedClientVersions()
  const ciphers = selectedCiphers()

  log(`Start simulation — server=${mode} attacker=${attacker} speed=${speed}ms`)
  renderMessage('Client', `ClientHello: versions=[${versions.join(', ')}] ciphers=[${ciphers.join(', ')}]`)

  setTimeout(()=>{
    if(attacker){
      log('Attacker: observed ClientHello — stripping TLS 1.3/TLS 1.2 from list (simulation)')
      renderMessage('Network (attacker)', 'Modified ClientHello: versions=[TLS 1.1, TLS 1.0]')
    } else {
      renderMessage('Network', 'ClientHello forwarded unchanged')
    }
  }, speed)

  setTimeout(()=>{
    // server chooses based on mode and what it sees
    let serverSelected = null
    if(mode === 'modern'){
      // prefers TLS 1.3/1.2
      serverSelected = (attacker ? ['TLS 1.1','TLS 1.0'] : versions).find(v => ['TLS 1.3','TLS 1.2','TLS 1.1','TLS 1.0'].includes(v)) || 'TLS 1.2'
    } else {
      serverSelected = (attacker ? ['TLS 1.1','TLS 1.0'] : versions).find(v => v === 'TLS 1.0') || 'TLS 1.0'
    }

    const chosenCipher = (attacker && ciphers.includes('3DES')) ? '3DES' : (ciphers[0]||'AES-GCM')
    renderMessage('Server', `ServerHello: selected_version=${serverSelected}; selected_cipher=${chosenCipher}`)
    log(`Server selected ${serverSelected} / ${chosenCipher}`)

    // client reaction
    setTimeout(()=>{
      if(versions.includes(serverSelected)){
        renderMessage('Client', `Accepts ${serverSelected} — handshake proceeds`)
        resultEl.className = 'result ok'
        resultEl.textContent = `Negotiated: ${serverSelected} / ${chosenCipher}`
        log(`Handshake complete: negotiated ${serverSelected}`)
      } else {
        // client falls back (simulated)
        renderMessage('Client', `Did not find ${serverSelected} in offered versions — client may fallback`) 
        // determine fallback behavior
        if(versions.some(v=>v < serverSelected) || versions.length>0){
          renderMessage('Client', `Client retries with lower versions (simulated)`) 
          // For simplicity, assume it finally accepts serverSelected
          resultEl.className = 'result warn'
          resultEl.textContent = `ALERT: Negotiated legacy version ${serverSelected} — weak` 
          log(`Negotiation resulted in weak ${serverSelected}`)
        } else {
          resultEl.className='result warn'
          resultEl.textContent = `Handshake failed — no compatible versions` 
          log('Handshake failed: incompatible versions')
        }
      }
    }, speed)

  }, speed*2)
}

runBtn.addEventListener('click', ()=>{
  runBtn.disabled = true
  simulateSequence()
  setTimeout(()=>{ runBtn.disabled = false }, 2200)
})

resetBtn.addEventListener('click', clear)

copyLogs.addEventListener('click', ()=>{
  navigator.clipboard?.writeText(logArea.textContent).then(()=>{
    alert('Logs copied to clipboard')
  }).catch(()=>{
    alert('Copy failed — select the log and copy manually')
  })
})

// initial view
clear()
renderMessage('Client', 'ClientHello: versions=[TLS 1.3, TLS 1.2] ciphers=[AES-GCM]')
resultEl.className='result ok'
resultEl.textContent='Click Simulate to run a handshake'
