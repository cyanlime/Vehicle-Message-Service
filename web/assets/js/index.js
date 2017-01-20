/*var October=[
            {'date':'2016-10-01','time':'11:05:08','distance':'1850','useTime':'00:05:26'},
            {'date':'2016-10-01','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2016-10-01','time':'15:05:08','distance':'1880','useTime':'00:04:26'}
        ];
var November=[
            {'date':'2015-11-15','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2015-11-15','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2015-11-15','time':'15:05:08','distance':'1880','useTime':'00:04:26'}
        ];
var December=[
           
            {'date':'2016-12-21','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2016-12-21','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2016-12-21','time':'15:05:08','distance':'1880','useTime':'00:04:26'},
            {'date':'2016-12-21','time':'15:05:08','distance':'1880','useTime':'00:04:26'}
        ];*/

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
            getCurrentDate(token);
            //getCurrentTrail(token,response);
        }
    });
}

//时间戳转换
function dateFormat(time,type){
    /*
        time:需要转换的时间   
        type：true or false  true显示小时分秒  反之
    */
    function fillZero(v){
        if(v<10){v='0'+v;}
        return v;
    }
    if(type){
        var d = new Date(parseInt(time) * 1000);
        var year=d.getFullYear(); 
        var month=fillZero(d.getMonth()+1); 
        var date=fillZero(d.getDate()); 
        var hour=d.getHours(); 
        var minute=d.getMinutes(); 
        var second=d.getSeconds(); 
        return year+"-"+month+"-"+date+"    "+hour+":"+minute+":"+second;
    }else{
        var d = new Date(parseInt(time) * 1000);
        d = [d.getFullYear(), fillZero(d.getMonth()+1), fillZero(d.getDate())];
        return d;
    }
}

//获取url参数
function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]); return null;
}

//获取当前日期
function getCurrentDate(token) {
    $.ajax({
        type: 'GET',
        url: '/nav/current_time/',
        headers: {
            'Authorization': token
        },
        success: function (response) {
            var date = dateFormat(response.result.current_time,false);
            var dateStr = date.join('-');
            var dateParameter = date.join('');
            $('#beginTime').html(dateStr);
            getCurrentTrail(token,dateParameter);
        }
    });
}

//获取行驶轨迹
function getCurrentTrail(token,dateParameter) {
    var data={};
    data.date = dateParameter;

    $.ajax({
        type: 'POST',
        url: '/nav/series_point/',
        data:JSON.stringify(data),
        headers: {
            'Authorization': token
        },
        success: function (response) {
            buildPanel(response);
        }
    });
}


//加载date插件
$(function(){
    $('#beginTime').date(null,searchRoute,err);
});

//选择失败函数
function err(){
    alert('请重新选择日期');
}

//选择时间成功执行函数
function searchRoute(datestr){

    //buildPanel(October,November,December,datestr);
   
}

function buildPanel(response){
    var str = [];
    var data = response.result.account;
    var date = dateFormat(response.result.account.create_time,true);
    str.push('<div class="content">'+
                    '<div class="row">'+
                        '<span>'+date+'</span>'+
                    '</div>'+
                    '<div class="row font">'+
                        '<span>里程：'+'</span>'+
                        '<span>&nbsp耗时'+'</span>'+
                    '</div>'+
                '</div>'
            )

    //现在一条，以后会多条
    /*for(var i=0;i<ary.length;i++){
        str.push('<div class="content">'+
                    '<div class="row">'+
                        '<span>'+ary[i].date+'</span>'+
                        '<span>&nbsp'+ary[i].time+'</span>'+
                    '</div>'+
                    '<div class="row font">'+
                        '<span>里程：'+ary[i].distance+'</span>'+
                        '<span>&nbsp耗时'+ary[i].useTime+'</span>'+
                    '</div>'+
                '</div>'
            )
    }*/
    $('#panel').html(str);
    $("#noinfo").addClass("hide");
    map();

    function map(){
        $('.content').click(function(){
            window.location.href='map_track.html';
        })
    }

/*    if(datestr == '2016-10-01'){
        buildDom(October);
    }else if(datestr == '2015-11-15'){
        buildDom(November);
    }else if(datestr == '2016-12-21'){
        buildDom(December);
    }else{
        $("#noinfo").removeClass("hide");
    }*/
   
}












