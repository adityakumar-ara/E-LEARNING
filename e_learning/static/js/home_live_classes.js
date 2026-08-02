function updateHomeLiveCTAs(){
    const now = new Date();
    document.querySelectorAll('.home-live-card').forEach(card => {
        const start = new Date(card.dataset.start);
        const end = new Date(card.dataset.end);
        const meeting = card.dataset.meeting;
        const courseUrl = card.dataset.courseUrl;
        const enrolled = card.dataset.enrolled === '1';
        const cta = card.querySelector('.home-live-cta-btn');
        const ctaText = card.querySelector('.home-live-cta-text');
        const countdown = card.querySelector('.home-live-countdown');

        if(!cta || !ctaText || !countdown) return;

        const isToday = now.toDateString() === start.toDateString();
        const isDailyActive = now >= start && now <= end;
        const isBeforeToday = now < start;
        const isAfterToday = now > end;

        if(isAfterToday){
            cta.className = 'btn btn-secondary w-100 home-live-cta-btn';
            cta.disabled = true;
            ctaText.innerText = 'Session Ended';
            countdown.innerText = '';
            return;
        }

        if(isDailyActive){
            if(enrolled && meeting){
                cta.className = 'btn btn-primary w-100 home-live-cta-btn';
                cta.disabled = false;
                ctaText.innerText = 'Join Now';
                cta.onclick = () => window.open(meeting, '_blank');
                countdown.innerText = '';
            } else {
                cta.className = 'btn btn-primary w-100 home-live-cta-btn';
                cta.disabled = false;
                ctaText.innerText = 'Enroll to Join';
                cta.onclick = () => window.location.href = courseUrl;
                countdown.innerText = '';
            }
            return;
        }

        const diff = isBeforeToday ? start - now : start - now;
        if(diff > 0){
            const totalSeconds = Math.floor(diff / 1000);
            const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
            const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
            const seconds = String(totalSeconds % 60).padStart(2, '0');

            cta.className = 'btn btn-secondary w-100 home-live-cta-btn';
            cta.disabled = true;
            ctaText.innerText = 'Wait';
            countdown.innerText = `Starts in ${hours}:${minutes}:${seconds}`;
        } else {
            cta.className = 'btn btn-secondary w-100 home-live-cta-btn';
            cta.disabled = true;
            ctaText.innerText = 'Wait';
            countdown.innerText = '';
        }
    });
}

document.addEventListener('DOMContentLoaded', function(){
    updateHomeLiveCTAs();
    setInterval(updateHomeLiveCTAs, 1000);
});
