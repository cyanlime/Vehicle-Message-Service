
//获取url参数
function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]); return null;
}

//获取当前车机位置信息
function getCurrentPoint(token) {
    $.ajax({
        type: 'GET',
        url: '/nav/current_point/',
        headers: {
            'Authorization': token
        },
        success: function (response) {
            displayQueryResults(response)
        }
    });
}

/*高德地图api*/
var map = new AMap.Map("container", {
    resizeEnable: true,
    zoom: 18
});

function regeocoder(response) {  //逆地理编码
    var resData = response.result;
    var lnglatXY = [resData.longitude, resData.latitude];
    var geocoder = new AMap.Geocoder({
        radius: 1000,
        extensions: "all"
    });
    geocoder.getAddress(lnglatXY, function (status, result) {
        if (status === 'complete' && result.info === 'OK') {
            geocoder_CallBack(result);
        }
    });
    var marker = new AMap.Marker({  //加点
        map: map,
        position: lnglatXY
    });
    map.setFitView();
}

function geocoder_CallBack(data) {
    var address = data.regeocode.formattedAddress; //返回地址描述
    document.getElementById("position-result").innerHTML = address;
}


//页面显示判断
function displayQueryResults(response){
    if(response.errcode == 201){
        $('#result').css('dispiay','none');
        $('#no-result').css('dispiay','block');
    }else{
        regeocoder(response);
    }
}


window.onload = function () {
    var code = getQueryString('code');
    if (code == undefined) {
        return;
    }
    var data = JSON.stringify({
        code: code
    });
    $.ajax({
        type: 'POST',
        url: '/account/wechat_sign_in/',
        data: data,
        dataType: 'json',
        contentType: 'application/json',
        success: function (response) {
            $('#console').text(JSON.stringify(response));
            var token = response.token;
            if (token == undefined) {
                return;
            }
            getCurrentPoint(token);
        }
    });

    // $.ajax('/account/wechat_sign_in/', {
    //     code: code
    // }, function(response){
    //     $('#console').text(response);
    // });
}

/*var map = new AMap.Map("container", {
    resizeEnable: true,
    zoom: 18
}),
    lnglatXY = [116.396574, 39.992706];*/ //已知点坐标

/*function regeocoder() {  //逆地理编码
    var geocoder = new AMap.Geocoder({
        radius: 1000,
        extensions: "all"
    });
    geocoder.getAddress(lnglatXY, function (status, result) {
        if (status === 'complete' && result.info === 'OK') {
            geocoder_CallBack(result);
        }
    });
    var marker = new AMap.Marker({  //加点
        map: map,
        position: lnglatXY
    });
    map.setFitView();
}*/

/*function geocoder_CallBack(data) {
    var address = data.regeocode.formattedAddress; //返回地址描述
    document.getElementById("result").innerHTML = address;
}*/

