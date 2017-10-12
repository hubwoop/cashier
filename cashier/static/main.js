// https://codepen.io/znak/pen/aOvMOd


function already_listed_handler(identifier) {

    var already_listed = false;

    $("#receipt").children().each(function () {
        if (Number($(this).attr("data-id")) === identifier) {
            $(this).find("[data-ammount]").text(function (i, oldText) {
                return Number(oldText) + 1
            });
            already_listed = true;
        }
    });

    return already_listed;
}

function add_new_item_to_receipt(identifier) {
    $.getJSON("/get/item/" + identifier, function (result) {
        var receipt = $("#receipt");
        receipt.append(
            "<li data-id="
            + result['id']
            + "><dl><dt>Amount: <span data-ammount>1</span></dt><dt>Item: "
            + result['title']
            + "</dt><dd>Price: "
            + result['price']
            + "€</dd></dl></li>");
    });
}

function update_receipt_with(identifier) {
    if (!already_listed_handler(identifier)){
        add_new_item_to_receipt(identifier)
    }
}

document.addEventListener('DOMContentLoaded', function () {

    contrast();
    $('.itemTitle').click(function () {

        update_receipt_with(Number($(this).attr('id')))

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