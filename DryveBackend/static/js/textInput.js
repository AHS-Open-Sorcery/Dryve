function focusInput(input) {
    $(`label[for=${$(input).attr('id')}]`).addClass('active');
}

function unfocusInput(input) {
    if($(input).val().length === 0)
        $(`label[for=${$(input).attr('id')}]`).removeClass('active');
}
