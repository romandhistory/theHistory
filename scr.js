document.addEventListener('DOMContentLoaded', async function () {
    const slidesRoot = document.getElementById('slidesRoot');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalClose = document.querySelector('.modal-close');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const tabButtons = document.querySelectorAll('.tab-button');
    const modalHeader = document.querySelector('.modal-header');
    const searchInput = document.querySelector('.slide-search');

    let slidesData = [];
    let swiper = null;
    let currentYearId = null;
    const yearCache = {};
    const sliderViewport = document.querySelector('.tranding-slider');
    let sliderScale = 1;
    const minSliderScale = 0.4;
    const sliderScaleStep = 0.08;
    let isSliderHovered = false;
    let pinchStartDistance = null;
    let pinchStartScale = 1;

    try {
        const response = await fetch('data/slides.json');
        slidesData = await response.json();
        renderSlides(slidesData);
        initSwiper();
        bindEvents();
        initSliderWheelBehavior();
        history.replaceState({ deepLink: false }, '', window.location.pathname + window.location.search + window.location.hash);
        handleDeepLink(true);
        window.addEventListener('hashchange', function () { handleDeepLink(true); });
        window.addEventListener('popstate', handlePopState);
    } catch (error) {
        console.error('Не удалось загрузить data/slides.json. Запустите через Live Server.', error);
    }

    function renderSlides(slides) {
        slidesRoot.innerHTML = slides.map(function (slide) {
            const lockedClass = slide.locked ? ' no-click' : '';
            const lockIcon = slide.locked ? '<span class="lock-icon">&#x1F512;</span>' : '';
            return (
                '<div class="swiper-slide tranding-slide' + lockedClass + '" data-year-id="' + slide.id + '" data-tag="' + slide.tag + '">' +
                '<img loading="lazy" src="' + slide.image + '" alt="' + escapeAttr(slide.label) + '">' +
                '<div class="tranding-slide-content">' +
                '<div class="tranding-slide-content-bottom">' +
                '<h2 class="event-name">' + escapeHtml(slide.label) + '</h2>' +
                '<h3>' + escapeHtml(slide.century) + '</h3>' +
                lockIcon +
                '</div></div></div>'
            );
        }).join('');
    }

    function initSwiper() {
        const defaultSlideIndex = slidesData.findIndex(function (slide) {
            return slide.tag === '871';
        });
        const isMobile = window.matchMedia('(max-width: 768px)').matches;

        swiper = new Swiper('.tranding-slider', {
            effect: isMobile ? 'slide' : 'coverflow',
            grabCursor: true,
            centeredSlides: true,
            initialSlide: defaultSlideIndex >= 0 ? defaultSlideIndex : 0,
            slidesPerView: 'auto',
            speed: isMobile ? 380 : 650,
            threshold: 8,
            touchRatio: 1,
            resistanceRatio: 0.7,
            allowTouchMove: true,
            followFinger: true,
            shortSwipes: true,
            longSwipes: true,
            longSwipesRatio: 0.3,
            longSwipesMs: 220,
            touchReleaseOnEdges: true,
            navigation: {
                nextEl: '.slide-arrow-next',
                prevEl: '.slide-arrow-prev'
            },
            freeMode: isMobile ? {
                enabled: true,
                sticky: true,
                momentum: true,
                momentumRatio: 0.95,
                momentumBounce: true,
                minimumVelocity: 0.02
            } : false,
            coverflowEffect: {
                rotate: 50,
                stretch: 0,
                depth: 100,
                modifier: 1,
                slideShadows: false
            }
        });

        swiper.on('slideChange', updateSlideSideClasses);
        updateSlideSideClasses();

        const prevArrow = document.querySelector('.slide-arrow-prev');
        const nextArrow = document.querySelector('.slide-arrow-next');
        if (prevArrow) {
            prevArrow.addEventListener('click', function () {
                if (swiper) swiper.slidePrev();
            });
        }
        if (nextArrow) {
            nextArrow.addEventListener('click', function () {
                if (swiper) swiper.slideNext();
            });
        }

        swiper.on('click', function (_swiperInstance, event) {
            const clickedSlide = event.target.closest('.swiper-slide');
            if (!clickedSlide) return;
            if (clickedSlide.classList.contains('no-click')) return;

            const slideIndex = Array.from(document.querySelectorAll('.swiper-slide')).indexOf(clickedSlide);
            if (!clickedSlide.classList.contains('swiper-slide-active')) {
                swiper.slideTo(slideIndex);
                return;
            }

            const yearId = clickedSlide.getAttribute('data-year-id');
            const slideName = clickedSlide.querySelector('.event-name').textContent;
            openModal(yearId, slideName);
        });
    }
    function initSliderWheelBehavior() {
        if (!sliderViewport) return;

        function applySliderScale() {
            sliderViewport.style.setProperty('--slider-scale', sliderScale.toFixed(3));
        }

        function clampScale(value) {
            return Math.min(1, Math.max(minSliderScale, value));
        }

        function getTouchDistance(touches) {
            if (touches.length < 2) return 0;
            const firstTouch = touches[0];
            const secondTouch = touches[1];
            const dx = secondTouch.clientX - firstTouch.clientX;
            const dy = secondTouch.clientY - firstTouch.clientY;
            return Math.hypot(dx, dy);
        }

        sliderViewport.addEventListener('mouseenter', function () {
            isSliderHovered = true;
        });

        sliderViewport.addEventListener('mouseleave', function () {
            isSliderHovered = false;
        });

        sliderViewport.addEventListener('wheel', function (event) {
            if (!isSliderHovered) return;

            const delta = event.deltaY || event.wheelDelta;
            if (delta > 0) {
                event.preventDefault();
                sliderScale = clampScale(sliderScale - sliderScaleStep);
                applySliderScale();
            } else if (delta < 0) {
                event.preventDefault();
                sliderScale = clampScale(sliderScale + sliderScaleStep);
                applySliderScale();
            }
        }, { passive: false });

        sliderViewport.addEventListener('touchstart', function (event) {
            if (event.touches.length === 2) {
                pinchStartDistance = getTouchDistance(event.touches);
                pinchStartScale = sliderScale;
                event.preventDefault();
            }
        }, { passive: false });

        sliderViewport.addEventListener('touchmove', function (event) {
            if (event.touches.length !== 2 || pinchStartDistance === null) return;

            event.preventDefault();
            const currentDistance = getTouchDistance(event.touches);
            const ratio = currentDistance / pinchStartDistance;
            sliderScale = clampScale(pinchStartScale * ratio);
            applySliderScale();
        }, { passive: false });

        sliderViewport.addEventListener('touchend', function (event) {
            if (event.touches.length < 2) {
                pinchStartDistance = null;
            }
        }, { passive: false });

        sliderViewport.addEventListener('touchcancel', function () {
            pinchStartDistance = null;
        });

        applySliderScale();
    }

    function updateSlideSideClasses() {
        if (!swiper) return;

        const slides = Array.from(document.querySelectorAll('.tranding-slide'));
        const activeIndex = swiper.activeIndex;
        const frontRange = 2;

        slides.forEach(function (slide, index) {
            slide.classList.remove('tranding-slide-left', 'tranding-slide-right', 'tranding-slide-front');

            if (index < activeIndex) {
                slide.classList.add('tranding-slide-left');
            } else if (index > activeIndex) {
                slide.classList.add('tranding-slide-right');
            }

            if (index >= activeIndex - frontRange && index <= activeIndex + frontRange) {
                slide.classList.add('tranding-slide-front');
            }
        });
    }
    async function openModal(yearId, slideName) {
        const slide = slidesData.find(function (s) { return s.id === yearId; });
        if (!slide || !slide.content) return;

        try {
            const yearData = await loadYear(yearId);
            currentYearId = yearId;
            modalTitle.textContent = 'Подробности о ' + slideName;
            modalContent.innerHTML = renderYearContent(yearId, yearData);
            resetTabState();
            setActiveTab(1);
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            modalHeader.style.paddingLeft = '20px';
            updateDeepLink(yearId, 1, 0);
        } catch (error) {
            console.error('Ошибка загрузки года ' + yearId, error);
        }
    }

    async function loadYear(yearId) {
        if (yearCache[yearId]) return yearCache[yearId];
        const slide = slidesData.find(function (s) { return s.id === yearId; });
        const response = await fetch(slide.content);
        const data = await response.json();
        yearCache[yearId] = data;
        return data;
    }

    function renderYearContent(yearId, yearData) {
        return (
            renderArticlesTab(yearId, 1, yearData.tabs.world) +
            renderArticlesTab(yearId, 2, yearData.tabs.russia) +
            renderGalleryTab(yearId, 3, yearData.tabs.gallery)
        );
    }

    function renderArticlesTab(yearId, tabNum, tabData) {
        const tabId = 'slide' + yearId + '-tab' + tabNum;
        let html = '<div class="tab-content" id="' + tabId + '">';

        if (tabData.intro) {
            html += tabData.intro;
        }

        if (tabData.articles && tabData.articles.length) {
            html += '<div class="multi-buttons">';
            tabData.articles.forEach(function (article, index) {
                const moreId = tabId + '-more' + (index + 1);
                html += '<button class="tab-more-button" data-more-id="' + moreId + '">' +
                    escapeHtml(article.button) + '</button>';
            });
            html += '</div>';

            tabData.articles.forEach(function (article, index) {
                html += renderArticle(tabId, index + 1, article);
            });
        }

        html += '</div>';
        return html;
    }

    function resolveTabNum(tab) {
        if (tab === 'russia' || tab === 2 || tab === '2') return 2;
        if (tab === 'gallery' || tab === 3 || tab === '3') return 3;
        return 1;
    }

    function renderArticleLinks(links) {
        if (!links || !links.length) return '';

        let html = '<div class="event-links">';
        links.forEach(function (link) {
            const tabNum = resolveTabNum(link.tab);
            const articleNum = link.article || 1;
            const label = link.label || (link.year + ' — событие ' + articleNum);
            html += '<button type="button" class="header-btn event-link-btn"' +
                ' data-year="' + escapeAttr(String(link.year)) + '"' +
                ' data-tab="' + tabNum + '"' +
                ' data-article="' + articleNum + '">' +
                escapeHtml(label) + '</button>';
        });
        html += '</div>';
        return html;
    }

    function renderArticle(tabId, index, article) {
        const moreId = tabId + '-more' + index;
        const linksHtml = renderArticleLinks(article.links);
        let html = '<div class="tab-more-content" id="' + moreId + '">';
        html += '<button class="tab-back-button"><ion-icon name="arrow-back"></ion-icon></button>';

        const hasRichLayout = article.title || article.image;
        if (hasRichLayout) {
            html += '<div class="content-with-image"><div class="content-text">';
            if (article.title) {
                html += '<h2>' + escapeHtml(article.title) + '</h2>';
            }
            article.body.forEach(function (p) { html += p; });
            html += linksHtml;
            html += '</div>';
            if (article.image) {
                html += '<div class="content-image"><img loading="lazy" src="' + article.image.src +
                    '" alt="' + escapeAttr(article.image.alt) + '"></div>';
            }
            html += '</div>';
        } else {
            article.body.forEach(function (p) { html += p; });
            html += linksHtml;
        }

        html += '</div>';
        return html;
    }

    function openArticleInModal(tabNum, articleIndex) {
        const tabId = 'slide' + currentYearId + '-tab' + tabNum;
        const tabContent = document.getElementById(tabId);
        const moreId = tabId + '-more' + articleIndex;

        resetTabState();
        setActiveTab(tabNum);

        if (tabContent) {
            const mainText = tabContent.querySelector(':scope > p');
            if (mainText) mainText.style.display = 'none';
            const buttonsContainer = tabContent.querySelector('.multi-buttons');
            if (buttonsContainer) buttonsContainer.style.display = 'none';
        }

        const target = document.getElementById(moreId);
        if (target) {
            target.classList.add('active');
            modalHeader.style.paddingLeft = '60px';
            const contentText = target.querySelector('.content-text');
            if (contentText) contentText.scrollTop = 0;
        }
    }

    async function navigateToEvent(yearId, tabNum, articleIndex, replaceStateFlag) {
        yearId = String(yearId);
        const slide = slidesData.find(function (s) { return s.id === yearId; });
        if (!slide || !slide.content) return;

        try {
            const yearData = await loadYear(yearId);
            currentYearId = yearId;
            modalTitle.textContent = 'Подробности о ' + slide.label;
            modalContent.innerHTML = renderYearContent(yearId, yearData);
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            modalHeader.style.paddingLeft = '20px';

            if (articleIndex && articleIndex > 0) {
                openArticleInModal(tabNum, articleIndex);
            } else {
                resetTabState();
                setActiveTab(tabNum);
            }

            const slideIndex = slidesData.findIndex(function (s) { return s.id === yearId; });
            if (swiper && slideIndex >= 0) swiper.slideTo(slideIndex);

            updateDeepLink(yearId, tabNum, articleIndex, replaceStateFlag);
        } catch (error) {
            console.error('Ошибка перехода к событию ' + yearId, error);
        }
    }

    function renderGalleryTab(yearId, tabNum, gallery) {
        const tabId = 'slide' + yearId + '-tab' + tabNum;
        const isMobile = window.matchMedia('(max-width: 768px)').matches;
        let html = '<div class="tab-content" id="' + tabId + '"><div class="photo-gallery">';
        gallery.forEach(function (item) {
            const sizeClass = item.size && !isMobile ? ' photo-card--' + item.size : '';
            const caption = item.caption ? item.caption : item.alt ? item.alt : '';
            html += '<div class="photo-card' + sizeClass + '"><img loading="lazy" src="' + item.src +
                '" alt="' + escapeAttr(item.alt) + '">';
            if (caption) {
                html += '<div class="photo-caption">' + escapeHtml(caption) + '</div>';
            }
            html += '</div>';
        });
        html += '</div></div>';
        return html;
    }

    function resetTabState() {
        modalContent.querySelectorAll('.tab-content').forEach(function (content) {
            content.classList.remove('active');
            content.querySelectorAll('.tab-more-content').forEach(function (more) {
                more.classList.remove('active');
            });
            const mainText = content.querySelector(':scope > p');
            if (mainText) mainText.style.display = 'block';
            const buttonsContainer = content.querySelector('.multi-buttons');
            if (buttonsContainer) buttonsContainer.style.display = 'grid';
        });
    }

    function setActiveTab(tabNum) {
        tabButtons.forEach(function (button, index) {
            const tabId = 'slide' + currentYearId + '-tab' + (index + 1);
            button.setAttribute('data-tab', tabId);
            button.classList.toggle('active', index === tabNum - 1);
        });
        const activeTab = document.getElementById('slide' + currentYearId + '-tab' + tabNum);
        if (activeTab) activeTab.classList.add('active');
    }

    function resetTabContent(tabContent) {
        tabContent.querySelectorAll('.tab-more-content').forEach(function (more) {
            more.classList.remove('active');
        });
        const mainText = tabContent.querySelector(':scope > p');
        if (mainText) mainText.style.display = 'block';
        const buttonsContainer = tabContent.querySelector('.multi-buttons');
        if (buttonsContainer) buttonsContainer.style.display = 'grid';
    }

    function closeModal(pushHistory) {
        if (pushHistory instanceof Event) pushHistory = false;
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        currentYearId = null;
        const cleanedUrl = window.location.pathname + window.location.search;
        if (pushHistory === true) {
            history.pushState({ deepLink: false }, '', cleanedUrl);
        } else {
            history.replaceState({ deepLink: false }, '', cleanedUrl);
        }
    }

    function updateDeepLink(yearId, tabNum, articleIndex, replaceStateFlag) {
        if (!yearId) return;

        const params = new URLSearchParams();
        params.set('year', yearId);

        if (tabNum && tabNum !== 1) {
            params.set('tab', tabNum === 2 ? 'russia' : String(tabNum));
        }
        if (articleIndex && articleIndex > 0) {
            params.set('article', String(articleIndex));
        }

        let newHash = '';

        if (tabNum === 1) {
            newHash = yearId;
            if (articleIndex && articleIndex > 0) {
                newHash += '/' + articleIndex;
            }
        } else if (tabNum === 2) {
            newHash = yearId + '/russia';
            if (articleIndex && articleIndex > 0) {
                newHash += '/' + articleIndex;
            }
        } else if (tabNum === 3) {
            newHash = yearId + '/gallery';
            if (articleIndex && articleIndex > 0) {
                newHash += '/' + articleIndex;
            }
        } else {
            if (params.toString()) {
                newHash = '#' + params.toString();
            }
        }

        if (newHash && newHash[0] !== '#') {
            newHash = '#' + newHash;
        }
        const newUrl = window.location.pathname + window.location.search + newHash;
        const state = {
            deepLink: true,
            yearId: String(yearId),
            tabNum: tabNum || 1,
            articleIndex: typeof articleIndex === 'number' ? articleIndex : 0
        };

        if (replaceStateFlag) {
            history.replaceState(state, '', newUrl);
        } else {
            history.pushState(state, '', newUrl);
        }
    }

    function parseDeepLinkHash() {
        const rawHash = window.location.hash.replace(/^#/, '');
        if (!rawHash) return {};

        let yearId = null;
        let tab = null;
        let article = null;

        if (rawHash.includes('=') || rawHash.includes('&')) {
            const params = new URLSearchParams(rawHash);
            yearId = params.get('year') || params.get('id') || rawHash;
            tab = params.get('tab');
            if (tab === '3') tab = 'gallery';
            article = params.get('article');
        } else {
            const segments = rawHash.split('/').filter(Boolean);
            yearId = segments[0] || null;
            if (segments.length === 2) {
                if (/^\d+$/.test(segments[1])) {
                    article = segments[1];
                } else {
                    tab = segments[1];
                }
            } else if (segments.length >= 3) {
                tab = segments[1];
                if (tab === '3') tab = 'gallery';
                article = segments[2];
            }
        }

        return {
            yearId,
            tabNum: resolveTabNum(tab || 1),
            articleIndex: article ? parseInt(article, 10) || 0 : 0
        };
    }

    function handleDeepLink(replaceHistory) {
        const { yearId, tabNum, articleIndex } = parseDeepLinkHash();
        if (!yearId) return;

        const slideIndex = slidesData.findIndex(function (slide) { return slide.id === yearId; });
        if (slideIndex === -1) return;

        if (swiper) swiper.slideTo(slideIndex);
        navigateToEvent(yearId, tabNum, articleIndex, replaceHistory);
    }

    function handlePopState(event) {
        const state = event.state;
        if (state && state.deepLink) {
            if (swiper) {
                const slideIndex = slidesData.findIndex(function (slide) { return slide.id === state.yearId; });
                if (slideIndex >= 0) swiper.slideTo(slideIndex);
            }
            navigateToEvent(state.yearId, state.tabNum, state.articleIndex, true);
            return;
        }

        if (window.location.hash) {
            handleDeepLink(true);
            return;
        }

        if (modalOverlay.classList.contains('active')) {
            closeModal(false);
        }
    }

    function bindEvents() {
        modalClose.addEventListener('click', function () { closeModal(false); });

        modalOverlay.addEventListener('click', function (e) {
            if (e.target === modalOverlay) closeModal(false);
        });

        tabButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                const tabId = button.getAttribute('data-tab');
                tabButtons.forEach(function (btn) { btn.classList.remove('active'); });
                modalContent.querySelectorAll('.tab-content').forEach(function (content) {
                    content.classList.remove('active');
                    resetTabContent(content);
                });
                button.classList.add('active');
                const tab = document.getElementById(tabId);
                if (tab) tab.classList.add('active');
                modalHeader.style.paddingLeft = '20px';

                const activeTabMatch = tabId.match(/slide\d+-tab(\d+)/);
                const activeTabNum = activeTabMatch ? parseInt(activeTabMatch[1], 10) : 1;
                updateDeepLink(currentYearId, activeTabNum, 0);
            });
        });

        modalContent.addEventListener('click', function (event) {
            const moreButton = event.target.closest('.tab-more-button');
            if (moreButton) {
                const tabContent = moreButton.closest('.tab-content');
                const moreId = moreButton.getAttribute('data-more-id');
                const tabMatch = tabContent.id.match(/slide\d+-tab(\d+)/);
                const articleIndexMatch = moreId.match(/more(\d+)/);
                const tabNum = tabMatch ? parseInt(tabMatch[1], 10) : 1;
                const articleIndex = articleIndexMatch ? parseInt(articleIndexMatch[1], 10) : 1;
                const mainText = tabContent.querySelector(':scope > p');
                if (mainText) mainText.style.display = 'none';
                const buttonsContainer = tabContent.querySelector('.multi-buttons');
                if (buttonsContainer) buttonsContainer.style.display = 'none';
                const target = document.getElementById(moreId);
                if (target) target.classList.add('active');
                modalHeader.style.paddingLeft = '60px';
                updateDeepLink(currentYearId, tabNum, articleIndex);
                return;
            }

            const eventLink = event.target.closest('.event-link-btn');
            if (eventLink) {
                navigateToEvent(
                    eventLink.getAttribute('data-year'),
                    parseInt(eventLink.getAttribute('data-tab'), 10),
                    parseInt(eventLink.getAttribute('data-article'), 10)
                );
                return;
            }

            const backButton = event.target.closest('.tab-back-button');
            if (backButton) {
                const tabContent = backButton.closest('.tab-content');
                resetTabContent(tabContent);
                modalHeader.style.paddingLeft = '20px';
                const activeTabButton = Array.from(tabButtons).find(function (button) {
                    return button.classList.contains('active');
                });
                if (activeTabButton) {
                    const activeTabMatch = activeTabButton.getAttribute('data-tab').match(/slide\d+-tab(\d+)/);
                    const activeTabNum = activeTabMatch ? parseInt(activeTabMatch[1], 10) : 1;
                    updateDeepLink(currentYearId, activeTabNum, 0);
                }
                return;
            }

            const card = event.target.closest('.photo-card');
            if (card && card.closest('.photo-gallery')) {
                const gallery = card.closest('.photo-gallery');
                const activeCard = gallery.querySelector('.photo-card.expanded');
                if (activeCard && activeCard !== card) activeCard.classList.remove('expanded');
                card.classList.toggle('expanded');
                document.body.classList.toggle('photo-modal-open', !!document.querySelector('.photo-card.expanded'));
            }
        });

        document.body.addEventListener('click', function (event) {
            if (event.target.closest('.photo-card') || event.target.closest('.photo-gallery')) return;
            const expandedCard = document.querySelector('.photo-card.expanded');
            if (expandedCard) {
                expandedCard.classList.remove('expanded');
                document.body.classList.remove('photo-modal-open');
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') return;
            const expandedCard = document.querySelector('.photo-card.expanded');
            if (expandedCard) {
                expandedCard.classList.remove('expanded');
                document.body.classList.remove('photo-modal-open');
                return;
            }
            if (modalOverlay.classList.contains('active')) closeModal();
        });

        searchInput.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            const tag = searchInput.value.trim();
            const slideIndex = Array.from(document.querySelectorAll('.swiper-slide'))
                .findIndex(function (slide) { return slide.getAttribute('data-tag') === tag; });
            if (slideIndex !== -1) {
                swiper.slideTo(slideIndex);
                searchInput.value = '';
            }
        });

        const mainBtn = document.getElementById('mainBtn');
        if (mainBtn) {
            mainBtn.addEventListener('click', function () {
                location.reload();
            });
        }

        const headingLink = document.querySelector('.section-heading__link');
        if (headingLink) {
            headingLink.addEventListener('click', function (event) {
                event.preventDefault();
                location.reload();
            });
        }
    }

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function escapeAttr(text) {
        return escapeHtml(text).replace(/"/g, '&quot;');
    }
});
