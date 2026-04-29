// static/custom_admin.js

document.addEventListener("DOMContentLoaded", function() {
    // Lấy phần tử input ngày/giờ từ trang quản trị
    var inputNgayQuet = document.getElementById('id_ngay_quet__range__gte');

    // Lấy giá trị hiện tại của input
    var currentValue = inputNgayQuet.value;

    // Sử dụng regex để thay đổi định dạng của giá trị thành '00:00'
    var formattedValue = currentValue.replace(/(\d{2}\/\d{2}\/\d{4}) \w{2}:\d{2}/, '$1 00:00');
    console.log(formattedValue)

    // Đặt lại giá trị của input thành giá trị đã được định dạng lại
    inputNgayQuet.value = formattedValue;
});
