from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class Account(BaseModel):
    id: int
    userName: str
    type: int
    status: int
    whitelistAuthority: int
    createTime: int
    tokenVersion: int
    ban: int
    baoyueVersion: int
    donateVersion: int
    vipType: int
    anonimousUser: bool
    paidFee: bool


class Profile(BaseModel):
    userId: int
    userType: int
    nickname: str
    avatarImgId: int
    avatarUrl: str
    backgroundImgId: int
    backgroundUrl: str
    signature: str
    createTime: int
    userName: str
    accountType: int
    shortUserName: str
    birthday: int
    authority: int
    gender: int
    accountStatus: int
    province: int
    city: int
    authStatus: int
    description: Optional[str] = None
    detailDescription: Optional[str] = None
    defaultAvatar: bool
    expertTags: Optional[list] = None
    experts: Optional[list] = None
    djStatus: int
    locationStatus: int
    vipType: int
    followed: bool
    mutual: bool
    authenticated: bool
    lastLoginTime: int
    lastLoginIP: str
    remarkName: Optional[str] = None
    viptypeVersion: int
    authenticationTypes: int
    avatarDetail: Optional[Any] = None
    anchor: bool


class LoginStatusResponse(BaseModel):
    code: int
    account: Account
    profile: Profile
