from typing import List, Optional, Any
from pydantic import BaseModel

QUALITY_LIST = [
    "dolby",
    "jymaster",
    "sky",
    "jyeffect",
    "hires",
    "lossless",
    "exhigh",
    "standard",
]  # 从高到低
QUALITY_INDEX = {q: i for i, q in enumerate(QUALITY_LIST)}


class Artist(BaseModel):
    id: int
    name: str
    tns: List[Any] = []
    alias: List[Any] = []


class Album(BaseModel):
    id: int
    name: str
    picUrl: str
    tns: List[Any] = []
    pic_str: Optional[str] = None
    pic: int


class QualityInfo(BaseModel):
    br: int
    fid: int
    size: int
    vd: float
    sr: int


class NoCopyrightRcmd(BaseModel):
    type: int
    typeDesc: str
    songId: Optional[Any] = None
    thirdPartySong: Optional[Any] = None
    expInfo: Optional[Any] = None


class Song(BaseModel):
    name: str
    id: int
    pst: int
    t: int
    ar: List[Artist]
    alia: List[str] = []
    pop: float
    st: int
    rt: Optional[str] = None
    fee: int
    v: int
    crbt: Optional[Any] = None
    cf: str
    al: Album
    dt: int
    h: Optional[QualityInfo] = None
    m: Optional[QualityInfo] = None
    l: Optional[QualityInfo] = None
    sq: Optional[QualityInfo] = None
    hr: Optional[QualityInfo] = None
    a: Optional[Any] = None
    cd: str
    no: int
    rtUrl: Optional[Any] = None
    ftype: int
    rtUrls: List[Any] = []
    djId: int
    copyright: int
    s_id: int
    mark: int
    originCoverType: int
    originSongSimpleData: Optional[Any] = None
    tagPicList: Optional[Any] = None
    resourceState: bool
    version: int
    songJumpInfo: Optional[Any] = None
    entertainmentTags: Optional[Any] = None
    awardTags: Optional[Any] = None
    displayTags: Optional[Any] = None
    markTags: List[Any] = []
    single: int
    noCopyrightRcmd: Optional[NoCopyrightRcmd] = None
    mv: int
    rtype: int
    rurl: Optional[Any] = None
    mst: int
    cp: int
    publishTime: int
    mainTitle: Optional[str] = None
    additionalTitle: Optional[str] = None

    @property
    def is_cloud_no_match(self) -> bool:
        """通过云盘上传的音乐，网易云不存在公开对应"""
        return self.t == 1

    @property
    def is_cloud_match(self) -> bool:
        """通过云盘上传的音乐，网易云存在公开对应"""
        return self.t == 2

    @property
    def is_free_or_no_copyright(self) -> bool:
        """免费或无版权"""
        return self.fee == 0

    @property
    def is_vip(self) -> bool:
        """VIP 歌曲"""
        return self.fee == 1

    @property
    def is_album_purchase(self) -> bool:
        """购买专辑"""
        return self.fee == 4

    @property
    def is_vip_or_free_low(self) -> bool:
        """非会员可免费播放低音质，会员可播放高音质及下载"""
        return self.fee == 8

    @property
    def can_buy_single(self) -> bool:
        """可单独购买 2 元单曲"""
        return self.fee == 1 or self.fee == 8

    @property
    def has_mv(self) -> bool:
        """是否有MV"""
        return self.mv != 0

    @property
    def is_stereo(self) -> bool:
        """立体声"""
        return (self.mark & 8192) != 0

    @property
    def is_instrumental(self) -> bool:
        """纯音乐"""
        return (self.mark & 131072) != 0

    @property
    def is_dolby_atmos(self) -> bool:
        """支持 杜比全景声(Dolby Atmos)"""
        return (self.mark & 262144) != 0

    @property
    def is_explicit(self) -> bool:
        """脏标 🅴"""
        return (self.mark & 1048576) != 0

    @property
    def is_hi_res(self) -> bool:
        """支持 Hi-Res"""
        return (self.mark & 17179869184) != 0

    @property
    def is_original(self) -> bool:
        """原曲"""
        return self.originCoverType == 1

    @property
    def is_cover(self) -> bool:
        """翻唱"""
        return self.originCoverType == 2

    @property
    def is_dj_program(self) -> bool:
        """是DJ节目"""
        return self.djId != 0


class ChargeInfo(BaseModel):
    rate: int
    chargeUrl: Optional[Any] = None
    chargeMessage: Optional[Any] = None
    chargeType: int


class FreeTrialPrivilege(BaseModel):
    resConsumable: bool
    userConsumable: bool
    listenType: Optional[Any] = None
    cannotListenReason: Optional[Any] = None
    playReason: Optional[Any] = None
    freeLimitTagType: Optional[Any] = None


class Privilege(BaseModel):
    id: int
    fee: int
    payed: int
    st: int
    pl: int
    dl: int
    sp: int
    cp: int
    subp: int
    cs: bool
    maxbr: int
    fl: int
    toast: bool
    flag: int
    preSell: bool
    playMaxbr: int
    downloadMaxbr: int
    maxBrLevel: str
    playMaxBrLevel: str
    downloadMaxBrLevel: str
    plLevel: str
    dlLevel: str
    flLevel: str
    rscl: Optional[Any] = None
    freeTrialPrivilege: FreeTrialPrivilege
    rightSource: int
    chargeInfoList: List[ChargeInfo]
    code: int
    message: Optional[Any] = None
    plLevels: Optional[Any] = None
    dlLevels: Optional[Any] = None
    ignoreCache: Optional[Any] = None
    bd: Optional[Any] = None

    @property
    def is_copyright_restricted(self) -> bool:
        """由于版权保护，您所在的地区暂时无法使用"""
        return self.toast

    @property
    def is_grey(self) -> bool:
        """灰色歌曲"""
        return self.st < 0
    



    def resolve_level(self, user_level: str, target_level: str) -> str:
        if user_level not in QUALITY_INDEX:
            return target_level # 未知音质等级，返回目标音质等级，有可能是"none"
        if target_level not in QUALITY_INDEX:
            return user_level
        return QUALITY_LIST[max(
            QUALITY_INDEX[user_level],
            QUALITY_INDEX[target_level],
        )]
        
    def resolve_pl_level(self, target: str) -> str:
        """最大当前用户可试听音质"""
        return self.resolve_level(self.plLevel, target)

    def resolve_dl_level(self, target: str) -> str:
        """最大当前用户可下载音质"""
        return self.resolve_level(self.dlLevel, target)
    
    def resolve_fl_level(self, target: str) -> str:
        """最大免费用户可播放音质"""
        return self.resolve_level(self.flLevel, target)
    
    def resolve_max_br_level(self, target: str) -> str:
        """该音乐最高音质"""
        return self.resolve_level(self.maxBrLevel, target)
    
    



class SongDetailResponse(BaseModel):
    songs: List[Song]
    privileges: List[Privilege]
    code: int


class SongDetailResponseOnlyOne(BaseModel):
    song: Song
    privilege: Privilege
    code: int
