// static/amap_events.js
// 初始化地图对象
var map = new AMap.Map("map_container", {
    resizeEnable: true,
    zoom: 11,
    center: [116.397428, 39.90923] // 默认北京
});

// 示例事件：点击提示经纬度
map.on('click', function(e){
    alert('您点击的位置: ' + e.lnglat.getLng() + ',' + e.lnglat.getLat());
});

// 你可以在这里继续加入标记、绘制、后端API交互等功能