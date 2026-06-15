<template>
    <div class="card mb-3 border-info">
        <div
            class="card-header d-flex justify-content-between align-items-center"
            style="cursor: pointer;"
            @click="expanded = !expanded"
            :aria-expanded="expanded"
            aria-controls="privacy-notice-body"
        >
            <span class="fw-bold text-info">
                <i class="bi bi-info-circle me-2"></i>Privacy Notice
            </span>
            <i :class="expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        </div>
        <Transition
            @before-enter="beforeEnter"
            @enter="enter"
            @leave="leave"
        >
            <div v-if="expanded">
                <div class="card-body">
                    <p>
                        The Department of Biodiversity, Conservation and Attractions (DBCA) collects this personal
                        information to assess, approve and grant an Apiary Authority that allows you to
                        legally carry out beekeeping activities in Western Australia's national parks, conservation
                        reserves and certain Crown lands for beekeeping.
                    </p>
                    <p>
                        You are required to provide this information under the
                        <em>Conservation and Land Management Act 1984</em> and
                        <em>Conservation and Land Management Regulations 2002</em>.
                    </p>
                    <p>
                        If you choose not to provide personal information, you will not be able to legally carry
                        out beekeeping activities in Western Australia's national parks, conservation reserves and
                        certain Crown lands for beekeeping.
                    </p>
                    <p>
                        For further details on how DBCA manage your personal information, you can read our
                        <a href="#privacy-policy-url-placeholder" target="_blank">Privacy Policy</a>.
                        If you have any questions about how your personal information will be handled, or if you
                        would like to access your personal information, please email
                        <a href="mailto:privacy@dbca.wa.gov.au">privacy@dbca.wa.gov.au</a>.
                    </p>
                </div>
            </div>
        </Transition>
    </div>
</template>

<script>
export default {
    name: 'PrivacyNotice',
    data() {
        return {
            expanded: true,
        };
    },
    methods: {
        beforeEnter(el) {
            el.style.height = '0';
            el.style.overflow = 'hidden';
        },
        enter(el, done) {
            el.style.transition = 'height 0.3s ease';
            el.style.height = el.scrollHeight + 'px';
            el.addEventListener('transitionend', () => {
                el.style.height = '';
                el.style.overflow = '';
                done();
            }, { once: true });
        },
        leave(el, done) {
            el.style.height = el.scrollHeight + 'px';
            el.style.overflow = 'hidden';
            el.offsetHeight; // force reflow
            el.style.transition = 'height 0.3s ease';
            el.style.height = '0';
            el.addEventListener('transitionend', done, { once: true });
        },
    },
};
</script>
