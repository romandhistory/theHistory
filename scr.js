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

    try {
        const response = await fetch('data/slides.json');
        slidesData = await response.json();
        renderSlides(slidesData);
        initSwiper();
        bindEvents();
    } catch (error) {
        console.error('Не удалось загрузить data/slides.json. Запустите через Live Server.', error);
    }

    function renderSlides(slides) {
        slidesRoot.innerHTML = slides.map(function (slide) {
            const lockedClass = slide.locked ? ' no-click' : '';
            const lockIcon = slide.locked ? '<span class="lock-icon">&#x1F512;</span>' : '';
            return (
                '<div class="swiper-slide tranding-slide' + lockedClass + '" data-year-id="' + slide.id + '" data-tag="' + slide.tag + '">' +
                '<img src="' + slide.image + '" alt="' + escapeAttr(slide.label) + '">' +
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
            return slide.tag === '19';
        });
        swiper = new Swiper('.tranding-slider', {
            effect: 'coverflow',
            grabCursor: true,
            centeredSlides: true,
            initialSlide: defaultSlideIndex >= 0 ? defaultSlideIndex : 0,
            slidesPerView: 'auto',
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
    function updateSlideSideClasses() {
        if (!swiper) return;

        const slides = Array.from(document.querySelectorAll('.tranding-slide'));
        const activeIndex = swiper.activeIndex;

        slides.forEach(function (slide, index) {
            slide.classList.remove('tranding-slide-left', 'tranding-slide-right');
            if (index < activeIndex) {
                slide.classList.add('tranding-slide-left');
            } else if (index > activeIndex) {
                slide.classList.add('tranding-slide-right');
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
                html += '<div class="content-image"><img src="' + article.image.src +
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

    async function navigateToEvent(yearId, tabNum, articleIndex) {
        yearId = String(yearId);
        const slide = slidesData.find(function (s) { return s.id === yearId; });
        if (!slide || !slide.content) return;

        try {
            const yearData = await loadYear(yearId);
            currentYearId = yearId;
            modalTitle.textContent = 'Подробности о ' + slide.label;
            modalContent.innerHTML = renderYearContent(yearId, yearData);
            openArticleInModal(tabNum, articleIndex);

            const slideIndex = slidesData.findIndex(function (s) { return s.id === yearId; });
            if (swiper && slideIndex >= 0) swiper.slideTo(slideIndex);
        } catch (error) {
            console.error('Ошибка перехода к событию ' + yearId, error);
        }
    }

    function renderGalleryTab(yearId, tabNum, gallery) {
        const tabId = 'slide' + yearId + '-tab' + tabNum;
        let html = '<div class="tab-content" id="' + tabId + '"><div class="photo-gallery">';
        gallery.forEach(function (item) {
            const sizeClass = item.size ? ' photo-card--' + item.size : '';
            const caption = item.caption ? item.caption : item.alt ? item.alt : '';
            html += '<div class="photo-card' + sizeClass + '"><img src="' + item.src +
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

    function closeModal() {
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        currentYearId = null;
    }

    function bindEvents() {
        modalClose.addEventListener('click', closeModal);

        modalOverlay.addEventListener('click', function (e) {
            if (e.target === modalOverlay) closeModal();
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
            });
        });

        modalContent.addEventListener('click', function (event) {
            const moreButton = event.target.closest('.tab-more-button');
            if (moreButton) {
                const tabContent = moreButton.closest('.tab-content');
                const moreId = moreButton.getAttribute('data-more-id');
                const mainText = tabContent.querySelector(':scope > p');
                if (mainText) mainText.style.display = 'none';
                const buttonsContainer = tabContent.querySelector('.multi-buttons');
                if (buttonsContainer) buttonsContainer.style.display = 'none';
                const target = document.getElementById(moreId);
                if (target) target.classList.add('active');
                modalHeader.style.paddingLeft = '60px';
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
