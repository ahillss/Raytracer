
# jitter

## ver 1

```glsl
//from gamedev.stackexchange.com/questions/26789

vec2 jitter(vec2 offset, float d) {
    for(int i=0;i<32;i++) {
        offset=rand2(offset)*d;

        if((offset.x*offset.y)>(d*d)) {
            break;
        }
    }

    return offset;
}

vec2 offset=fragCoord.xy;

vec3 rf=normalize(reflect(rd,n));

mat3 rfmat=rotMatFromNormal(n,rf);

offset=jitter(offset,0.025);
vec3 jj=normalize(rfmat*vec3(offset.x,offset.y,1.0));

```
## ver 2

```glsl

float drefl=material->diffuseRefl;
float xoffs, yoffs;

do {
    xoffs=rand()*drefl;
    yoffs=rand()*drefl;

} while((xoffs*xoffs+yoffs*yoffs)>(drefl*drefl));

vec3 Ra=RN1*xoffs;
vec3 Rb=RN2*yoffs*drefl;
vec3 R=normalize(reflectVec+Ra+Rb);

```

## ver 3

```glsl

do {
    x = 2.0*rand()-1.0;
    y = 2.0*rand()-1.0;
} while ( x*x+y*y > 1.0 );

r = tan(theta); //theta is max angle from the z axis (cone's width is 2*theta)
Vector v(r*x, r*y, 1);
v.Normalize();


```
