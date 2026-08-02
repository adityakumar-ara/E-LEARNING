// Enable client-side toggle so Join appears exactly at class start time
function parseIsoDate(value){
    if(!value) return null;
    const parsed = new Date(value);
    if(!isNaN(parsed.getTime())) return parsed;

    const match = value.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2}):(\d{2})/);
    if(!match) return null;

    const [_, year, month, day, hour, minute, second, tzSign, tzOffset] = match;
    const offsetMinutes = parseInt(tzOffset, 10);
    const offset = offsetMinutes * (tzSign === '+' ? 1 : -1);
    const utc = Date.UTC(year, month - 1, day, hour, minute, second);
    return new Date(utc - offset * 60000);
}

function updateLiveCTAs(){
    const now = new Date();
    const liveRow = document.getElementById('live-now-list');
    const upcomingRow = document.getElementById('upcoming-list');
    const liveCount = document.getElementById('live-count');
    const upcomingCount = document.getElementById('upcoming-count');

    const cards = document.querySelectorAll('.live-now-card, .upcoming-class-card');
    cards.forEach(card => {
        const start = parseIsoDate(card.dataset.start);
        const end = parseIsoDate(card.dataset.end);
        const meeting = card.dataset.meeting;
        const courseUrl = card.dataset.courseUrl || '#';
        const enrolled = card.dataset.enrolled === '1';
        const cta = card.querySelector('.cta-btn');
        if(!cta || !start || !end) return;

        const wrapper = card.closest('[data-card-container]');
        const isLive = now.getTime() >= start.getTime() && now.getTime() <= end.getTime();
        const isUpcoming = now.getTime() < start.getTime();
        const isEnded = now.getTime() > end.getTime();

        if(isEnded && wrapper){
            wrapper.remove();
            return;
        }

        if(isLive && upcomingRow && liveRow && wrapper && upcomingRow.contains(wrapper)){
            liveRow.appendChild(wrapper);
        } else if(isUpcoming && upcomingRow && liveRow && wrapper && liveRow.contains(wrapper)){
            upcomingRow.appendChild(wrapper);
        }

        if(isLive){
            if(enrolled && meeting){
                makeJoinButton(cta, meeting);
            } else if(!enrolled){
                makeEnrollButton(cta, courseUrl);
            } else {
                setButtonState(cta, 'waiting');
            }
        } else if(isUpcoming){
            setButtonState(cta, 'waiting');
        } else if(isEnded){
            setButtonState(cta, 'ended');
        }
    });

    let liveTotal = 0;
    let upcomingTotal = 0;
    cards.forEach(card => {
        const start = parseIsoDate(card.dataset.start);
        const end = parseIsoDate(card.dataset.end);
        if(!start || !end) return;
        const isLive = now.getTime() >= start.getTime() && now.getTime() <= end.getTime();
        const isUpcoming = now.getTime() < start.getTime();
        if(isLive) liveTotal += 1;
        else if(isUpcoming) upcomingTotal += 1;
    });

    if(liveCount) liveCount.textContent = liveTotal;
    if(upcomingCount) upcomingCount.textContent = upcomingTotal;
}

function makeJoinButton(cta, meeting){
    if(cta.tagName.toLowerCase() !== 'a'){
        const link = document.createElement('a');
        link.className = 'btn btn-primary w-100 cta-btn';
        link.href = meeting;
        link.target = '_blank';
        link.innerHTML = '<i class="bi bi-camera-video-fill me-2"></i> Join Now';
        cta.replaceWith(link);
    } else {
        cta.className = 'btn btn-primary w-100 cta-btn';
        cta.href = meeting;
        cta.target = '_blank';
        cta.innerHTML = '<i class="bi bi-camera-video-fill me-2"></i> Join Now';
    }
}

function makeEnrollButton(cta, courseUrl){
    if(cta.tagName.toLowerCase() !== 'a'){
        const link = document.createElement('a');
        link.className = 'btn btn-primary w-100 cta-btn';
        link.href = courseUrl;
        link.innerHTML = '<i class="bi bi-journal-plus me-2"></i> Enroll to Join';
        cta.replaceWith(link);
    } else {
        cta.className = 'btn btn-primary w-100 cta-btn';
        cta.href = courseUrl;
        cta.innerHTML = '<i class="bi bi-journal-plus me-2"></i> Enroll to Join';
    }
}

function setButtonState(cta, state){
    const tag = cta.tagName.toLowerCase();
    const text = {
        coming_soon: 'Coming Soon',
        enroll: 'Enroll to Join',
        waiting: 'Wait',
        ended: 'Session Ended'
    }[state] || 'Wait';

    if(tag === 'a'){
        const btn = document.createElement('button');
        btn.className = 'btn btn-secondary w-100 cta-btn';
        btn.disabled = true;
        btn.innerText = text;
        cta.replaceWith(btn);
    } else {
        cta.className = 'btn btn-secondary w-100 cta-btn';
        cta.disabled = true;
        cta.innerText = text;
    }
}

document.addEventListener('DOMContentLoaded', function(){
    updateLiveCTAs();
    setInterval(updateLiveCTAs, 1000);
});
