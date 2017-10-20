# raytracing snippets

Some useful snippets for raytracing.

## intersections
```glsl
bool intersectPlane(vec3 P,vec3 V,vec4 plane, out float t) {
    //Ax+By+Cz+D=0
    float NPd=dot(plane.xyz,P)+plane.w;
    
    //P not below/on
    if(NPd<=0.0) {
        return false;
    }
    
    float NV=dot(plane.xyz,V);
    
    //V not parallel/away
    if(NV>=0.0) {
        return false;
    }
    
    t=-NPd/NV;
    return true;
}

bool intersectSphere(vec3 P,vec3 V,vec3 C,float r,out float t) {
    vec3 M=P-C;
    float c=dot(M,M)-r*r;
    
    //P inside
    if(c<0.0) {
        return false;
    }
    
    float b=dot(V,M);
    
    //V away
    if(b > 0.0) {
        return false;
    }
    
    float d=b*b-c;
    
    //V towards but misses (no real roots)
    if(d < 0.0) {
        return false;
    }
    
    t=-b-sqrt(d);
    return true;
}

vec3 sphereNormal(vec3 ro, vec3 rd, vec3 c,vec3 colPt) {
    return normalize(colPt-c);
}

//from physically based rendering, ch 3.1.2, ray-bounds intersections
//from shadertoy.com/view/ld23DV

bool intersectBox(vec3 P,vec3 invV,vec3 bMin,vec3 bMax, out float t,out vec3 nor) {
    vec3 tmin = (bMin - P) * invV;
    vec3 tmax = (bMax - P) * invV;
    vec3 tnear = min(tmin, tmax);
    vec3 tfar = max(tmin, tmax);
    float enter = max(tnear.x, max(tnear.y, tnear.z)); //max(tnear.x, 0.0)
    float exit = min(tfar.x, min(tfar.y, tfar.z));
    t=enter;
    nor = -sign(invV)*step(tnear.yzx,tnear)*step(tnear.zxy,tnear);
    return exit > max(enter, 0.0); //exit>0.0 && enter<exit
}

bool intersectBoxP(vec3 P,vec3 invV,vec3 bMin,vec3 bMax, out float t) {
    vec3 tmin = (bMin - P) * invV;
    vec3 tmax = (bMax - P) * invV;
    vec3 tnear = min(tmin, tmax);
    vec3 tfar = max(tmin, tmax);
    float enter = max(tnear.x, max(tnear.y, tnear.z));
    float exit = min(tfar.x, min(tfar.y, tfar.z));
    t=enter;
    return exit > max(enter, 0.0);
}

bool intersectInvBox(vec3 P,vec3 invV,vec3 bMin,vec3 bMax, out float t,out vec3 nor) {
    vec3 tmin=(bMin-P)*invV;
    vec3 tmax=(bMax-P)*invV;
    vec3 tnear=min(tmin,tmax);
    vec3 tfar=max(tmin,tmax);
    float enter=max(tnear.x,max(tnear.y,tnear.z));
    float exit=min(tfar.x,min(tfar.y,tfar.z));
    t=exit;
    vec3 tfarEps=tfar+vec3(1e-4);
    nor=normalize(-sign(invV)*step(tfar,tfarEps.yzx)*step(tfar,tfarEps.zxy));
    return exit>max(enter,0.0); 
}

//alternative
// if(abs(dot(hit,xAxis)-dot(bMin,xAxis))<eps){return -xAxis;}
// if(abs(dot(hit,xAxis)-dot(bMax,xAxis))<eps){return xAxis;}

vec3 boxNormal(vec3 bMin,vec3 bMax, vec3 pt) {
    return normalize(step(abs(pt-bMax),vec3(1e-5))-step(abs(pt-bMin),vec3(1e-5)));
}

//from book: Physically Based Rendering

bool intersectTriangle(vec3 ro,vec3 rd,vec3 p0,vec3 p1,vec3 p2,out vec2 bcOut,out float tOut) {
    //Compute s1
    vec3 e1 = p1 - p0;
    vec3 e2 = p2 - p0;
    vec3 s1 = cross(rd, e2);
    float divisor = dot(s1, e1);

    if (divisor == 0.0) {
        return false;
    }

    float invDivisor = 1.0 / divisor;
    
    //Compute first barycentric coordinate
    vec3 d = ro - p0;
    float b1 = dot(d, s1) * invDivisor;
    
    if(b1 < 0.0 || b1 > 1.0) {
        return false;
    }
    
    //Compute second barycentric coordinate
    vec3 s2 = cross(d, e1);
    float b2 = dot(rd, s2) * invDivisor;
    
    if (b2 < 0.0 || b1 + b2 > 1.0) {
        return false;
    }
    
    //Compute t to intersection point
    float t = dot(e2, s2) * invDivisor;
            
    //
    tOut = t;
    bcOut=vec2(b1,b2);
    return true;
}

float fromBarycentric(float b1,float b2,float a0,float a1,float a2) {
    return (1.0-b1-b2 )*a0+b1*a1+b2*a2;
}

vec2 fromBarycentric(float b1,float b2,vec2 a0,vec2 a1,vec2 a2) {
    return (1.0-b1-b2 )*a0+b1*a1+b2*a2;
}

vec3 fromBarycentric(float b1,float b2,vec3 a0,vec3 a1,vec3 a2) {
    return (1.0-b1-b2 )*a0+b1*a1+b2*a2;
}

vec4 fromBarycentric(float b1,float b2,vec4 a0,vec4 a1,vec4 a2) {
    return (1.0-b1-b2 )*a0+b1*a1+b2*a2;
}
```

## rotations
```glsl
mat3 rotateAt(vec3 eye,vec3 at,vec3 up) {
  vec3 z=normalize(eye-at);
  vec3 x=normalize(cross(up,z));
  vec3 y=normalize(cross(z,x));
  return mat3(x,y,z);
}

mat3 lookRot(float yaw,float pitch) {
    vec2 s=vec2(sin(pitch),sin(yaw));
    vec2 c=vec2(cos(pitch),cos(yaw));
    return mat3(c.y,0.0,-s.y,s.y*s.x,c.x,c.y*s.x,s.y*c.x,-s.x,c.y*c.x);
}

mat3 orbitRot(float yaw,float pitch) {
    vec2 s=vec2(sin(pitch),sin(yaw));
    vec2 c=vec2(cos(pitch),cos(yaw));
    return mat3(c.y,0.0,-s.y, s.y*s.x,c.x,c.y*s.x, s.y*c.x,-s.x,c.y*c.x);
}

mat3 rotX(float a) {
    float c=cos(a);
    float s=sin(a);
    return mat3(1.0,0.0,0.0, 0.0,c,s, 0.0,-s,c);
}

mat3 rotY(float a) {
    float c=cos(a);
    float s=sin(a);
    return mat3(c,0.0,-s, 0.0,1.0,0.0, s,0.0,c);
}

mat3 rotZ(float a) {
    float c=cos(a);
    float s=sin(a);
    return mat3(c,s,0.0, -s,c,0.0, 0.0,0.0,1.0);
}

//from neilmendoza.com/glsl-rotation-about-an-arbitrary-axis

mat3 rotAxis(vec3 axis,float angle) {
    float s=sin(angle);
    float c=cos(angle);
    float oc=1.0-c;
    vec3 as=axis*s;
    mat3 p=mat3(axis*axis.x,axis*axis.y,axis*axis.z);    
    mat3 q=mat3(c,-as.z,as.y,as.z,c,-as.x,-as.y,as.x,c);
    return p*oc+q;
}

//

mat3 rotMatFromNormal(vec3 n,vec3 r) {
    //n=n.zyx*vec3(1.0,1.0,-1.0); //maybe helps if n==r
    vec3 a=normalize(cross(n,r));
    vec3 b=normalize(cross(a,r));
    mat3 m=mat3(a,b,r);
    return m;//for r
}
```

## patterns
```glsl
//from geeks3d.com/20140201/glsl-menger-sponge-raymarching-code-samples-updated

vec3 floor_color(in vec3 p, float scale,vec3 color0, vec3 color1, vec3 color2) {
  //p=abs(p);
  if(fract(p.x)>scale && fract(p.z)>scale) {
    if(mod((floor(p.x)+floor(p.z)),2.0) == 0.0) {
      return color0;
    } else {
      return color1;
    }
  } else {
    return color2;
  }
}

//from OpenGL Shading Language 2ed

vec3 brickCol(vec3 localPos,vec3 BrickColor,vec3 MortarColor,vec3 BrickSize,vec3 BrickPct) {
    vec3 position=localPos/BrickSize.xyz;

    if(fract(position.y*0.5)>0.5){
		position.xz+=vec2(0.5);
    }

    position=fract(position);
    vec3 useBrick=step(position,BrickPct.xyz);

    //float ns1=noise(mod(localPos,1.0)*150.0);
    //float ns2=noise(mod(localPos,1.0)*100.0)*0.1;
	//abs(MortarColor-ns1*0.2),abs(BrickColor-ns1*0.05)
    return mix(MortarColor,BrickColor,useBrick.x*useBrick.y*useBrick.z);
}

//

vec3 checkerCol(vec3 texc, vec3 color0, vec3 color1) {
    float q=clamp(mod(dot(floor(texc),vec3(1.0)),2.0),0.0,1.0);
    return color1*q+color0*(1.0-q);
}
```

## texture mapping
```glsl
//from github.com/tunabrain/tungsten/blob/master/src/core/primitives/Skydome.cpp
// use linear for texture mag/min filters

vec2 dirToDomeUv(vec3 d) {
    //float sinTheta=sqrt(max(1.0-d.y*d.y,0.0));
    vec2 uv=vec2(atan2(d.z,d.x)/(2.0*PI)+0.5,acos(-d.y)/PI);
    //uv.y=uv.y*2.0-1.0; //when texture lacks below horizon
    return uv;
}

vec3 domeUvToDir(vec2 uv) {
    float phi=(uv.x-0.5)*2.0*PI;
    float theta=uv.y*PI;
    sinTheta =sin(theta);
    return vec3(cos(phi)*sinTheta,-cos(theta),sin(phi)*sinTheta);
}

vec2 genTexCoords(vec3 pt,vec3 nor,mat3 m) {
    //uv=vec2(dot(p,I),dot(p,J));
    return (m*(pt-nor*dot(pt,nor))).xy*0.1;
}
```

## random
```glsl
//from unknown

float rand(vec2 coordinate) {
    return fract(sin(dot(coordinate.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

//from unknown

vec2 rand2(vec2 co){
    vec2 r;
    r.x=fract(sin(dot(co.xy,vec2(12.9898,78.233)))*43758.5453);
    r.y=fract(cos(dot(co.xy,vec2(4.898,7.23)))*23421.631);
    return r;
}
```

## lights
```glsl
vec3 calcPtLightCol(vec3 P,vec3 N,vec3 lPos,vec3 lAtten,vec3 mCol,vec3 lCol,float shininess,float strength) {
    vec3 L=lPos.xyz-P;
    float lDist=length(L);
    L=L/lDist;
    float atten = 1.0/dot(lAtten,vec3(1.0,lDist,lDist*lDist));
    vec3 R=reflect(-L,N);
    float NdotL = max(0.0,dot(N,L));
    float NdotR = max(0.0, dot(N,R));
    float spec = (NdotL > 0.0)?pow(NdotR,shininess*128.0)*strength:0.0;
    float diffuse=NdotL;
    return lCol*(mCol*diffuse+spec)*atten;
}

//float spotCos=dot(L,-spotDir);
//atten*=(spotCos<spotCosCutoff)?0.0:pow(spotCos,spotExponent);
```

## misc
```glsl
vec3 orthog(vec3 a,vec3 b) {
    return normalize(a-b*dot(b,a)); //orthoganize a
}

float calcVecAngle(vec3 v0,vec3 v1) {
    float l=length(v0)*length(v1);
    float d=dot(v0,v1);
    return acos(d/l);
}

//from shadertoy.com/view/XdfGzS

float calcFlare(vec3 ro,vec3 rd,vec3 lightPos,float size) {
    vec3 viewLightDir=normalize(lightPos-ro);
    float viewLightDist=length(lightPos-ro);
    float q = dot(rd,viewLightDir)*0.5+0.5;
    float o = (1.0/viewLightDist)*size;
    return clamp(pow(q,900.0/o)*1.0,0.0,2.0);
}

//

#define PI 3.14159265359

//from en.wikipedia.org/wiki/Atan2#Definition_and_computation

float atan2(float y,float x) {  
    if(x>0.0) {
        return atan(y/x);
    } else if(y>0.0) {
        return PI/2.0-atan(x/y);
    } else if(y<0.0) {
        return -PI/2.0 -atan(x/y);
    } else if(x<0.0) {
        return atan(y/x)+PI;
    }

    return 0.0;
}

//from mzucker.github.io/2016/08/03/miniray.html

vec3 calcSky(vec3 d) {
    vec3 c=vec3(0.6,0.6,1.0)*pow(1.0-d.y*0.95,3.0);//top
    //c=(d.y<0.3)?min(c,vec3(0.6,0.6,1.0)*pow(1.0-d.x*0.01,18.0)):c;
    c=(d.y<0.9)?min(c,vec3(0.55,0.6,0.99)):c;//bottom
    return c;
}

//

float smooth_keyframe(float time,float frame0,float frame1,float val0,float val1) {
    float f=(time-frame0)/(frame1-frame0);
    return lerp(val0,val1,smoothStep(0.0,1.0,f));
}

```

## main
```glsl
vec3 render(vec3 ro,vec3 rd,vec2 uv) {
    return vec3(uv,0.5+0.5*sin(iTime));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float fovy=0.7854;
    float aspect=iResolution.x/iResolution.y;    
    vec2 ms=(iMouse.xy==vec2(0.0))?vec2(0.0):(iMouse.xy/iResolution.xy)*2.0-1.0;
    
    //mat3 viewRot=orbitRot(ms.x*2.0,ms.y*2.0);    
    //vec3 ro=viewRot*vec3(0.0,2.0,35.0);
        
    //mat3 viewRot=lookRot(ms.x*-3.0,ms.y*1.7);
    //vec3 ro=vec3(0.0,0.0,10.0);
    
    mat3 viewRot=mat3(1.0);
    vec3 ro=vec3(0.0);
    
    vec2 uv=fragCoord/iResolution.xy;
    vec2 scr=uv*2.0-1.0;
    vec3 primary=normalize(vec3(scr.x*aspect,scr.y,-1.0/tan(fovy/2.0)));
    vec3 rd=normalize(viewRot*primary);
    vec3 col=render(ro,rd,uv);
    
    col=mix(col,vec3(1.0),step(abs(floor(length(fragCoord-iMouse.xy))-3.0),0.0));

    fragColor=vec4(col,1.0);
}
```

## cursors
```glsl
//rounded square
col=mix(col,vec3(1.0),step(abs(floor(length(max(abs(fragCoord-iMouse.xy)-vec2(4.0),0.0)))-4.0),0.0));

//4 dots
col=mix(col,vec3(1.0),step(length(floor(abs(fragCoord-iMouse.xy))-vec2(4.0)),0.0));    

//4 circles
col=mix(col,vec3(1.0),step(abs(floor(length(abs(fragCoord-iMouse.xy)-vec2(4.0)))-1.0),0.0));
```
