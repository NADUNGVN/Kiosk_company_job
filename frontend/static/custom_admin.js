// static/custom_admin.js

document.addEventListener("DOMContentLoaded", function() {
    // Lấy tất cả các phần tử input trong bộ lọc ngày/giờ
    var dateInputs = document.querySelectorAll('.field-your_datetime_field input[type="text"]');
    
    // Định dạng lại giá trị của các input
    dateInputs.forEach(function(input) {
        // Tìm giá trị hiện tại của input
        var currentValue = input.value;
        
        // Định dạng lại giá trị thành định dạng mong muốn, ví dụ: 00:00
        var formattedValue = currentValue.replace(/\d\d:\d\d/, '00:00');
        
        // Đặt lại giá trị của input
        input.value = formattedValue;
    });
});
