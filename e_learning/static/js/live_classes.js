// Enable client-side toggle so Join appears exactly at class start time
function updateLiveCTAs(){
    const cards = document.querySelectorAll('[data-start]');
    const now = new Date();
    cards.forEach(card => {
        const start = new Date(card.getAttribute('data-start'));
        const end = new Date(card.getAttribute('data-end'));
        const meeting = card.getAttribute('data-meeting');
        const enrolled = card.getAttribute('data-enrolled') === '1';
        const cta = card.querySelector('.cta-btn');
        if(!cta) return;

        if(now >= start && now <= end){
            // class is live
            if(meeting && enrolled){
                // make CTA a join link
                cta.classList.remove('btn-secondary');
                cta.classList.remove('btn-outline-primary');
                cta.classList.add('btn-primary');
                if(cta.tagName.toLowerCase() !== 'a'){
                    const link = document.createElement('a');
                    link.className = cta.className + ' w-100 cta-btn';
                    link.href = meeting;
                    link.target = '_blank';
                    link.innerHTML = '<i class="bi bi-camera-video-fill me-2"></i> Join Now';
                    cta.replaceWith(link);
                } else {
                    cta.href = meeting;
                    cta.target = '_blank';
                    cta.innerHTML = '<i class="bi bi-camera-video-fill me-2"></i> Join Now';
                }
            } else if(!enrolled){
                // show enroll prompt
                if(cta.tagName.toLowerCase() === 'a'){
                    cta.href = cta.getAttribute('href') || cta.href;
                }
                cta.classList.remove('btn-secondary');
                cta.classList.remove('btn-outline-primary');
                cta.classList.add('btn-outline-primary');
                cta.innerText = 'Enroll to Join';
            }
        } else {
            // not live yet
            if(cta.tagName.toLowerCase() === 'a' && cta.classList.contains('btn-primary')){
                // replace with disabled wait button
                const btn = document.createElement('button');
                btn.className = 'btn btn-secondary w-100 cta-btn';
                btn.disabled = true;
                btn.innerText = 'Wait';
                cta.replaceWith(btn);
            } else {
                // ensure disabled wait shown
                cta.className = 'btn btn-secondary w-100 cta-btn';
                cta.disabled = true;
                cta.innerText = 'Wait';
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function(){
    updateLiveCTAs();
    // check every 10 seconds
    setInterval(updateLiveCTAs, 10000);
});
