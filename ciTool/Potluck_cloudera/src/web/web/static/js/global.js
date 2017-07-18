function get_ajax_content(url, data, control, error) {
    var $control = $(control);
    $.ajax({
        url : url,
        data : data,
        beforeSend : function(xhr, settings) {
            $control.html("<div class='alert alert-info'>Loading...</div>");
        }
    }).done(function(data, status, xhr) {
        $control.html(data);
    }).fail(function( jqXHR, textStatus, errorThrown ) {
        $control.html("<div class='alert alert-danger'>" + error + "<br/><br/>" + jqXHR.responseText.slice(0, 100) + "</div>");
    });
}

function get_testsuite_contents(path) {
    if ($("#id_suite_contents").length) {
        get_ajax_content("/suites/", {testsuite : path}, "#id_suite_contents", "Error while reading contents of '" + path + "'");
    }
}
function get_testbed_contents(path) {
    if ($("#id_testbed_contents").length) {
        get_ajax_content("/testbeds/", {testbed : path}, "#id_testbed_contents", "Error while reading contents of '" + path + "'");
    }
}

function show_confirm(opts) {
    defaults = {
        message : 'Are you sure you want to proceed',
        yes : null,
        redirect_url : '#'
    }
    var options = $.extend({}, defaults, opts);
    var $confirm_modal = $("#confirm-modal");

    // Show the message
    $confirm_modal.find(".modal-body").html(options.message);

    // Set the callback, if any
    if (options.yes) {
        $confirm_modal.find(".btn-primary").click(function(e) {
            options.yes(e);
        });
    }

    // Set the URL when the user clicks yes
    $confirm_modal.find(".btn-primary").attr("href", options.redirect_url);
    $confirm_modal.modal("show");
}

$(document).ready(function() {
    var $id_suite = $("#id_suite");
    var $id_testbed = $("#id_testbed");

    $id_suite.change(function(e) {
        var $selected_suite = $(this).find(":selected");
        if ($selected_suite.length) {
            var suite_path = $selected_suite.val();
            get_testsuite_contents(suite_path);
        }
    });

    $id_testbed.change(function(e) {
        var $selected_testbed = $(this).find(":selected");
        if ($selected_testbed.length) {
            var testbed = $selected_testbed.val();
            get_testbed_contents(testbed);
        }
    });
    $id_suite.change();
    $id_testbed.change();

    /* Show confirmation dialog before navigating from some links */
    var $confirm_modal = $("#confirm-modal");
    var $links = $("a[data-confirm-navigation='true']");
    $links.each(function () {
        $(this).click(function(e) {
            if ($(this).hasClass("btn-submit")) {
                return true;
            }
            e.preventDefault();
            var alert_message = $(this).attr("data-confirm-message");
            var url = $(this).attr("href");
            show_confirm({
                message : alert_message,
                redirect_url : url
            });
        });
    });

    /* Form submission with custom buttons */
    var $submit_buttons = $("a.btn-submit");
    $submit_buttons.each(function () {
        $(this).click(function(e) {
            e.preventDefault();
            var $this = $(this);
            var url = $this.attr("href");
            var $parent_form = $this.parents("form");

            // If confirm is required, interrupt the navigation
            if ($this.attr("data-confirm-navigation") == "true") {
                show_confirm({
                    message : $this.attr("data-confirm-message"),
                    yes : function() {
                        $parent_form.attr("action", url);   // Change the action url of the form
                        $parent_form.submit();
                    }
                });
            } else {
                $parent_form.attr("action", url);   // Change the action url of the form
                $parent_form.submit();
            }
        });
    });
});
