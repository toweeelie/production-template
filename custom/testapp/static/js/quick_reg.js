(function($) {
    $(document).ready(function(){
        $("#id_dropIn").click(function() {
            if($(this).prop('checked') == true) {
                $("#id_amountPaid").val(regParams.dropInPrice);
            } else {
                $("#id_amountPaid").val(regParams.basePrice);
            }	
        });
        $("#id_payLater").click(function() {
            if($(this).prop('checked') == true) {
                $("#id_amountPaid").prop("disabled", true);
                $("#id_receivedBy").prop("disabled", true);
            } else {
                $("#id_amountPaid").prop("disabled", false);
                $("#id_receivedBy").prop("disabled", false);
            }	
        });
    });
})(django.jQuery);
