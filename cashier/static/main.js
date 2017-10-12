// https://codepen.io/znak/pen/aOvMOd


function add_item_to_receipt(identifier) {
    $.getJSON("/get/item/" + identifier, function(result){
        var reciept = $("#receipt");
        reciept.append(
            "<li><dl><dt>Item: "
            + result['title']
            + "</dt><dd>Price: "
            + result['price']
            + "€</dd></dl></li>");
    });
}

document.addEventListener('DOMContentLoaded', function () {

    contrast();
    $('.itemTitle').click(function () {

        add_item_to_receipt(Number($(this).attr('id')))

    });

}, false);



function contrast() {

    var C, L, rgb;

    $(".colorBlock").each(function () {

        rgb = $(this).css('background-color');

        C = rgb.substr(4, rgb.length - 5).split(', ');

        for (var i = 0; i < C.length; ++i) {

            C[i] = Number(C[i]) / 255;

            if (C[i] <= 0.03928) {

                C[i] = C[i] / 12.92

            } else {

                C[i] = Math.pow(( C[i] + 0.055 ) / 1.055, 2.4);

            }

        }

        L = 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2];

        if (L > 0.179) {

            $(this).css('color', 'black');

        } else {

            $(this).css('color', 'white');

        }

    });

}