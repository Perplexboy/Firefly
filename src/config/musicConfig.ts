import type { MusicPlayerConfig } from "../types/config";

// 音乐播放器配置
export const musicPlayerConfig: MusicPlayerConfig = {
	// 禁用音乐播放器方法：
	// 模板默认侧边栏和导航栏两个都显示
	// 1. 侧边栏：在sidebarConfig.ts侧边栏配置把音乐组件enable设为false禁用即可
	// 2. 导航栏：在本配置文件把showInNavbar设为false禁用即可

	// 是否在导航栏显示音乐播放器入口
	showInNavbar: true,

	// 使用方式："meting" 使用 Meting API，"local" 使用本地音乐列表
	mode: "local",

	// 默认音量 (0-1)
	volume: 0.7,

	// 播放模式：'list'=列表循环, 'one'=单曲循环, 'random'=随机播放
	playMode: "list",

	// 是否显启用歌词
	showLyrics: true,

	// Meting API 配置
	meting: {
		// Meting API 地址
		// 默认使用官方 API，也可以使用自定义 API
		api: "https://api.i-meto.com/meting/api?server=:server&type=:type&id=:id&r=:r",
		// 音乐平台：netease=网易云音乐, tencent=QQ音乐, kugou=酷狗音乐, xiami=虾米音乐, baidu=百度音乐
		server: "netease",
		// 类型：song=单曲, playlist=歌单, album=专辑, search=搜索, artist=艺术家
		type: "playlist",
		// 歌单/专辑/单曲 ID 或搜索关键词
		id: "10046455237",
		// 认证 token（可选）
		auth: "",
		// 备用 API 配置（当主 API 失败时使用）
		fallbackApis: [
			"https://api.injahow.cn/meting/?server=:server&type=:type&id=:id",
			"https://api.moeyao.cn/meting/?server=:server&type=:type&id=:id",
		],
	},

	// 本地音乐配置（当 mode 为 'local' 时使用）
	// 1. 支持传入歌词文件的路径
	// lrc: "/assets/music/lrc/使一颗心免于哀伤-哼唱.lrc",
	// 2. 或者直接填入歌词字符串内容
	// lrc: "[00:00.00]歌词内容...",
	local: {
    playlist: [
        {
            name: "Friend",
            artist: "玉置浩二",
            url: "/assets/music/Friend-玉置浩二.flac",
            cover: "/assets/music/cover/玉置浩二-Friend.png",
            lrc: "/assets/music/lrc/Friend-玉置浩二.lrc",
        },
        // 添加新歌：
        {
            name: "1973",
            artist: "James Blunt",
            url: "/assets/music/1973-James Blunt.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/James Blunt-1973.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/1973-James Blunt.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
        {
            name: "Stand Out Fit In",
            artist: "ONE OK ROCK",
            url: "/assets/music/Stand Out Fit In-ONE OK ROCK.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/ONE OK ROCK-Stand Out Fit In.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Stand Out Fit In-ONE OK ROCK.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
        {
            name: "Brave Love, TIGA (PIANO VERSION)",
            artist: "矢野立美",
            url: "/assets/music/Brave Love, TIGA (PIANO VERSION)-矢野立美.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/矢野立美-Brave Love, TIGA (PIANO VERSION).png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Brave Love, TIGA (PIANO VERSION)-矢野立美.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
        {
            name: "Hotel California",
            artist: "Eagles",
            url: "/assets/music/Hotel California-Eagles.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Eagles-Hotel California.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Hotel California-Eagles.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
        {
            name: "No Woman, No Cry",
            artist: "Bob Marley",
            url: "/assets/music/No Woman, No Cry-Bob Marley.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Bob Marley-No Woman, No Cry.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/No Woman, No Cry-Bob Marley.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "Set Fire to the Rain",
            artist: "Adele",
            url: "/assets/music/Set Fire to the Rain-Adele.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Adele-Set Fire to the Rain.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Set Fire to the Rain-Adele.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "Should It Matter",
            artist: "Sissel",
            url: "/assets/music/Should It Matter-Sissel.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Sissel-Should It Matter.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Should It Matter-Sissel.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "The Left Panel",
            artist: "Buckethead",
            url: "/assets/music/The Left Panel-Buckethead.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Buckethead-The Left Panel.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/The Left Panel-Buckethead.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "Wonderful Tonight",
            artist: "Eric Clapton",
            url: "/assets/music/Wonderful Tonight-Eric Clapton.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Eric Clapton-Wonderful Tonight.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Wonderful Tonight-Eric Clapton.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "不让我的眼泪陪我过夜",
            artist: "齐秦",
            url: "/assets/music/不让我的眼泪陪我过夜-齐秦.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/齐秦-不让我的眼泪陪我过夜.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/不让我的眼泪陪我过夜-齐秦.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "黃昏",
            artist: "羅文",
            url: "/assets/music/黃昏-羅文.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/罗文-黄昏.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/黃昏-羅文.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "记事本",
            artist: "陈慧琳",
            url: "/assets/music/记事本-陈慧琳.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/陈慧琳-记事本.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/记事本-陈慧琳.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "寂靜的天空",
            artist: "HAYA",
            url: "/assets/music/寂靜的天空-HAYA.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/HAYA-寂靜的天空.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/寂靜的天空-HAYA.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "煎熬",
            artist: "李佳薇",
            url: "/assets/music/煎熬-李佳薇.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/李佳薇-煎熬.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/煎熬-李佳薇.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "梦醒时分",
            artist: "陈淑桦",
            url: "/assets/music/梦醒时分-陈淑桦.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/陈淑桦-梦醒时分.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/梦醒时分-陈淑桦.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "迷途羔羊",
            artist: "张震岳 & 大渊(顽童MJ116)",
            url: "/assets/music/迷途羔羊-张震岳 & 大渊(顽童MJ116).mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/张震岳-迷途羔羊.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/迷途羔羊-张震岳 & 大渊(顽童MJ116).lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "日落大道",
            artist: "梁博",
            url: "/assets/music/日落大道-梁博.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/梁博-日落大道.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/日落大道-梁博.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "涛声依旧",
            artist: "毛宁",
            url: "/assets/music/涛声依旧-毛宁.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/毛宁-涛声依旧.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/涛声依旧-毛宁.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "心ゆくまで",
            artist: "梅沢富美男",
            url: "/assets/music/心ゆくまで-梅沢富美男.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/梅沢富美男-心ゆくまで.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/心ゆくまで-梅沢富美男.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
		// 添加新歌：
		{
            name: "一人静",
            artist: "姬神",
            url: "/assets/music/一人静-姬神.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/姬神-一人静.png",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/一人静-姬神.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
        // 添加新歌：
		{
            name: "明天你是否依然爱我",
            artist: "童安格",
            url: "/assets/music/明天你是否依然爱我-童安格.mp3",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/童安格-明天你是否依然爱我.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/明天你是否依然爱我-童安格.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
        // 添加新歌：
		{
            name: "一场游戏一场梦",
            artist: "王杰",
            url: "/assets/music/一场游戏一场梦-王杰.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/王杰-一场游戏一场梦.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/一场游戏一场梦-王杰.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
        // 添加新歌：
		{
            name: "Haunt U (Prod.Mysticphonk)",
            artist: "Lil Peep",
            url: "/assets/music/Haunt U (Prod.Mysticphonk)-Lil Peep.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/Lil Peep-Haunt U (Prod.Mysticphonk).jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/Haunt U (Prod.Mysticphonk)-Lil Peep.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
        // 添加新歌：
		{
            name: "江上清风游",
            artist: "变奏的梦想",
            url: "/assets/music/江上清风游-变奏的梦想.flac",       // 放 public/assets/music/ 下
            cover: "/assets/music/cover/变奏的梦想-江上清风游.jpg",  // 放 public/assets/music/cover/ 下
            lrc: "/assets/music/lrc/江上清风游-变奏的梦想.lrc",  // 可选：歌词文件路径如 "/assets/music/lrc/歌词.lrc"，或直接写 LRC 字符串
        },
    ],
},
};
