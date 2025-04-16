
(function ($) {

    "use strict";

    var initPreloader = function () {
        $(document).ready(function ($) {
            var Body = $('body');
            Body.addClass('preloader-site');
        });
        // $(document).on('load', function () {
        //     $('.preloader-wrapper').fadeOut();
        //     $('body').removeClass('preloader-site');
        // });
        $('.preloader-wrapper').fadeOut();
        $('body').removeClass('preloader-site');
    }

    // init Chocolat light box
    var initChocolat = function () {
        // Chocolat(document.querySelectorAll('.image-link'), {
        //   imageSize: 'contain',
        //   loop: true,
        // })
    }

    var initSwiper = function () {

        var swiper = new Swiper(".main-swiper", {
            speed: 500,
            pagination: {
                el: ".swiper-pagination",
                clickable: true,
            },
            navigation: {
                nextEl: ".swiper-button-next",
                prevEl: ".swiper-button-prev",
            },
        });

        var category_swiper = new Swiper(".category-carousel", {
            slidesPerView: 6,
            spaceBetween: 30,
            speed: 500,
            navigation: {
                nextEl: ".category-carousel-next",
                prevEl: ".category-carousel-prev",
            },
            breakpoints: {
                0: {
                    slidesPerView: 2,
                },
                768: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 4,
                },
                1500: {
                    slidesPerView: 6,
                },
            }
        });

        var brand_swiper = new Swiper(".brand-carousel", {
            slidesPerView: 4,
            spaceBetween: 30,
            speed: 500,
            navigation: {
                nextEl: ".brand-carousel-next",
                prevEl: ".brand-carousel-prev",
            },
            breakpoints: {
                0: {
                    slidesPerView: 2,
                },
                768: {
                    slidesPerView: 2,
                },
                991: {
                    slidesPerView: 3,
                },
                1500: {
                    slidesPerView: 4,
                },
            }
        });

        var products_swiper = new Swiper(".products-carousel", {
            slidesPerView: 5,
            spaceBetween: 30,
            speed: 500,
            navigation: {
                nextEl: ".products-carousel-next",
                prevEl: ".products-carousel-prev",
            },
            breakpoints: {
                0: {
                    slidesPerView: 1,
                },
                768: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 4,
                },
                1500: {
                    slidesPerView: 6,
                },
            }
        });
    }

    var initProductQty = function () {

        $('.product-qty').each(function () {

            var $el_product = $(this);
            var quantity = 0;

            $el_product.find('.quantity-right-plus').click(function (e) {
                e.preventDefault();
                var quantity = parseInt($el_product.find('#quantity').val());
                $el_product.find('#quantity').val(quantity + 1);
            });

            $el_product.find('.quantity-left-minus').click(function (e) {
                e.preventDefault();
                var quantity = parseInt($el_product.find('#quantity').val());
                if (quantity > 0) {
                    $el_product.find('#quantity').val(quantity - 1);
                }
            });

        });

    }

    // init jarallax parallax
    var initJarallax = function () {
        // jarallax(document.querySelectorAll(".jarallax"));

        // jarallax(document.querySelectorAll(".jarallax-keep-img"), {
        //   keepImg: true,
        // });
    }



    var initSearch = function () {
        $(".catalog-btn").on("click", function () {
            // $(".catalog").toggleClass("active");
            // $(".catalog-btn").toggleClass("active");
            window.location.href = "/catalogue/category";
        });
    }

    var initLanguagePicker = function () {
        if (window.show_language_picker) {
            // frappe.call("frappe.translate.get_all_languages", {
            //     with_language_name: true
            // }).then((res) => {
            let language_list = [
                {
                    "language_code": "kk",
                    "language_name": "Қаз"
                },
                {
                    "language_code": "ru",
                    "language_name": "Рус"
                },
            ] //res.message;
            let language = frappe.get_cookie("preferred_language");
            let language_codes = [];
            let language_switcher = $(".lang-switch:first");
            language_list.forEach((language_doc) => {
                language_codes.push(language_doc.language_code);
                language_switcher.append(
                    $("<a class=\"lang px-2\"></a>").attr("value", language_doc.language_code).text(language_doc.language_name)
                );
            });
            language_switcher.removeClass("d-none");
            // language = language || (language_codes.includes(navigator.language) ? navigator.language : "en");
            language = language || "ru";
            language_switcher.val(language);
            document.documentElement.lang = language;
            language_switcher.find(`a[value="${language}"]`).addClass("selected");
            language_switcher.find("a").on("click", function (e) {
                e.preventDefault();
                const lang = $(this).attr("value");
                document.cookie = `preferred_language=${lang}`;
                window.location.reload();
            });
            // });
        }
    }

    // document ready
    $(document).ready(function () {

        initLanguagePicker();
        initPreloader();
        initSwiper();
        initProductQty();
        initJarallax();
        initChocolat();

    }); // End of a document

})(jQuery);