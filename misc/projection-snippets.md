# projections

## matrices

```glsl
mat4 frustum(float left,float right,float bottom,float top,float zNear,float zFar) {
    mat4 m=mat4(0.0);
    m[0][0]=(2.0*zNear)/(right-left);
    m[1][1]=(2.0*zNear)/(top-bottom);
    m[2][0]=(right+left)/(right-left);
    m[2][1]=(top+bottom)/(top-bottom);
    m[2][2]=-(zFar+zNear)/(zFar-zNear);
    m[2][3]=-1.0;
    m[3][2]=-(2.0*zFar*zNear)/(zFar-zNear);
    return m;
}

mat4 perspective_fovy(float fovy,float aspect,float zNear,float zFar) {
    float top=tan(fovy/2.0)*zNear;
    float right=top*aspect;
    return frustum(-right,right,-top,top,zNear,zFar);
}

//untested

mat4 ortho(float left,float right,float bottom,float top,float zNear,float zFar) { 
    mat4 m=mat4(1.0);
    m[0][0]=2.0/(right-left);
    m[1][1]=2.0/(top-bottom);
    m[2][2]=-2.0/(zFar-zNear);    
    m[3][0]=-(right+left)/(right-left);
    m[3][1]=-(top+bottom)/(top-bottom);
    m[3][2]=-(zFar+zNear)/(zFar-zNear);
    return m;
}

//

mat4 ortho2d(float left,float right,float bottom,float top) {
    return ortho(left,right,bottom,top,-1.0,1.0);
}

//

mat4 frustum_infinite(float left,float right,float bottom,float top,float zNear) {
    float ep=2.4e-7;
    mat4 m=mat4(0.0);
    m[0][0]=(2.0*zNear)/(right-left);
    m[1][1]=(2.0*zNear)/(top-bottom);
    m[2][0]=(right+left)/(right-left);
    m[2][1]=(top+bottom)/(top-bottom);
    m[2][2]=ep-1.0;//-(1.0-ep);
    m[2][3]=-1.0;
    m[3][2]=(ep-2.0)*zNear;//-((2.0-ep)*zNear);
    return m;
}
```

## misc

```glsl
float posToNdcDepth(float zpos,float zNear,float zFar) {
    float p22=zFar+zNear,p32=2.0*zFar*zNear; //perspective
    //float p22=2.0, p32=zNear-zFar; //ortho

    float clipZ=(zpos*p22+p32)/(zNear-zFar);
    float clipW=-zpos;
    float ndcZ = clipZ/clipW;

    return ndcZ;
}

float ndcToDepth(float ndcZ,float nearRange,float farRange) {
    return ((farRange-nearRange)*ndcZ + nearRange+farRange)/2.0;
}

vec3 depthToPos(mat4 invProjMat,vec2 scr,float depth) {
    vec3 ndcPos=vec3(scr,depth)*2.0-1.0; //the depth*2-1 for ndcToDepth(ndcZ,0,1)
    vec4 D=invProjMat*vec4(ndcPos,1.0);
    return D.xyz/D.w;
}

float linearDepth(float depth,float zNear,float zFar) {
    return (2.0*zNear)/(zFar+zNear-depth*(zFar-zNear));
}
```
