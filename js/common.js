
function decompressLZMA(c,progress) {
    return new Promise(function(resolve, reject) {
        LZMA.decompress(new Uint8Array(c), function(result, error) {
            if(result) {
                var buf = new ArrayBuffer(result.length);
                var bufView = new Uint8Array(buf);

                for (var i=0;i<result.length;i++) {
                    bufView[i] = result[i];
                }

                resolve(buf);
            } else {
                reject(error);
            }
        },progress);
    });
}

function createGLContext(canvas,params) {
    canvas.addEventListener("webglcontextcreationerror",(function(event) {
        setErrorMsg(String(event.statusMessage).replace(new RegExp('[,.]', 'g'),'\n'));
    }), false);

    canvas.addEventListener('webglcontextlost', function(e) {
        setErrorMsg("WebGL2 context lost.");
    }, false);

    try {
        var gl=canvas.getContext("webgl2",params);
        
        if(!gl) {
            gl=canvas.getContext("webgl",params);
        }
        
        return gl;
    } catch(e) {}

    setErrorMsg("Could not initialise WebGL2.");
    return null;
}

function createBindScreenGeometry(gl) {
    return (function(gl){
        var vao=gl.createVertexArray();
        var vertBuf=gl.createBuffer();

        gl.bindVertexArray(vao);
        gl.bindBuffer(gl.ARRAY_BUFFER,vertBuf);
        gl.bufferData(gl.ARRAY_BUFFER,(new Float32Array([-1,-1,1,-1,-1,1,1,1])),gl.STATIC_DRAW);
        gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
        gl.enableVertexAttribArray(0);

        function draw(w,h) {
            gl.viewport(0, 0, w,h);
            gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
        }

        return {"draw" :draw};
    })(gl);
}

function compileShader(gl,shader,src,onError) {
    gl.shaderSource(shader, src);
    gl.compileShader(shader);

    if(!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        var m=gl.getShaderInfoLog(shader);
        onError(m);
        return false;
    }

    return true;
}

function linkProgram(gl,prog,onError) {
    gl.linkProgram(prog);

    if(!gl.getProgramParameter(prog,gl.LINK_STATUS)) {
        var m=gl.getProgramInfoLog(prog);
        onError(m);
        return false;
    }

    return true;
}

function createProgram(gl,onError,header,footer) {
    var vsSrc="#version 300 es\nlayout(location=0) in vec2 a_pos;void main(){gl_Position=vec4(a_pos,0.0,1.0);}";
    var fsSrc="#version 300 es\nprecision lowp float;\nout vec4 outColor;\nvoid main(){outColor=vec4(vec3(0.0),1.0);}"

    var vs=gl.createShader(gl.VERTEX_SHADER);
    var fs=gl.createShader(gl.FRAGMENT_SHADER);
    var prog=gl.createProgram();

    if(!compileShader(gl,vs,vsSrc,onError) ||
       !compileShader(gl,fs,fsSrc,onError)) {
        return null;
    }

    gl.attachShader(prog,vs);
    gl.attachShader(prog,fs);


    if(!linkProgram(gl,prog,onError)) {
        return false;
    }

    return (function(gl,onError,prog,vs,fs,header,footer,uniformLocs){
        function setShader(src) {
            if(compileShader(gl,fs,"#version 300 es\n"+header+"\n#line 0\n"+src+"\n"+footer,onError)&&
               linkProgram(gl,prog,onError)){
                uniformLocs={};
                return true;
            }
            return false;
        }
        function useProgram() {
            gl.useProgram(prog);
        }
        function getUniformLoc(n) {
            if(!uniformLocs.hasOwnProperty(n)){
                uniformLocs[n]=gl.getUniformLocation(prog,n);
            }
            return uniformLocs[n];
        }

        function uniform1i(n,v){gl.uniform1i(getUniformLoc(n),v);}
        function uniform2i(n,v0,v1){gl.uniform2i(getUniformLoc(n),v0,v1);}
        function uniform3i(n,v0,v1,v2){gl.uniform3i(getUniformLoc(n),v0,v1,v2);}
        function uniform4i(n,v0,v1,v2,v3){gl.uniform4i(getUniformLoc(n),v0,v1,v2,v3);}

        function uniform1f(n,v){gl.uniform1f(getUniformLoc(n),v);}
        function uniform2f(n,v0,v1){gl.uniform2f(getUniformLoc(n),v0,v1);}
        function uniform3f(n,v0,v1,v2){gl.uniform3f(getUniformLoc(n),v0,v1,v2);}
        function uniform4f(n,v0,v1,v2,v3){gl.uniform4f(getUniformLoc(n),v0,v1,v2,v3);}

        function uniform1iv(n,v){gl.uniform1iv(getUniformLoc(n),v);}
        function uniform2iv(n,v){gl.uniform2iv(getUniformLoc(n),v);}
        function uniform3iv(n,v){gl.uniform3iv(getUniformLoc(n),v);}
        function uniform4iv(n,v){gl.uniform4iv(getUniformLoc(n),v);}

        function uniform1fv(n,v){gl.uniform1fv(getUniformLoc(n),v);}
        function uniform2fv(n,v){gl.uniform2fv(getUniformLoc(n),v);}
        function uniform3fv(n,v){gl.uniform3fv(getUniformLoc(n),v);}
        function uniform4fv(n,v){gl.uniform4fv(getUniformLoc(n),v);}

        function uniformMatrix2fv(n,t,v){gl.uniformMatrix2fv(getUniformLoc(n),t,v);}
        function uniformMatrix3x2fv(n,t,v){gl.uniformMatrix3x2fv(getUniformLoc(n),t,v);}
        function uniformMatrix4x2fv(n,t,v){gl.uniformMatrix4x2fv(getUniformLoc(n),t,v);}
        function uniformMatrix2x3fv(n,t,v){gl.uniformMatrix2x3fv(getUniformLoc(n),t,v);}
        function uniformMatrix3fv(n,t,v){gl.uniformMatrix3fv(getUniformLoc(n),t,v);}
        function uniformMatrix4x3fv(n,t,v){gl.uniformMatrix4x3fv(getUniformLoc(n),t,v);}
        function uniformMatrix2x4fv(n,t,v){gl.uniformMatrix2x4fv(getUniformLoc(n),t,v);}
        function uniformMatrix3x4fv(n,t,v){gl.uniformMatrix3x4fv(getUniformLoc(n),t,v);}
        function uniformMatrix4fv(n,t,v){gl.uniformMatrix4fv(getUniformLoc(n),t,v);}

        return {
            "set":setShader,
            "use":useProgram,

            "uniform1i":uniform1i,
            "uniform2i":uniform2i,
            "uniform3i":uniform3i,
            "uniform4i":uniform4i,

            "uniform1f":uniform1f,
            "uniform2f":uniform2f,
            "uniform3f":uniform3f,
            "uniform4f":uniform4f,

            "uniform1iv":uniform1iv,
            "uniform2iv":uniform2iv,
            "uniform3iv":uniform3iv,
            "uniform4iv":uniform4iv,

            "uniform1fv":uniform1fv,
            "uniform2fv":uniform2fv,
            "uniform3fv":uniform3fv,
            "uniform4fv":uniform4fv,

            "uniformMatrix2fv":uniformMatrix2fv,
            "uniformMatrix3x2fv":uniformMatrix3x2fv,
            "uniformMatrix4x2fv":uniformMatrix4x2fv,
            "uniformMatrix2x3fv":uniformMatrix2x3fv,
            "uniformMatrix3fv":uniformMatrix3fv,
            "uniformMatrix4x3fv":uniformMatrix4x3fv,
            "uniformMatrix2x4fv":uniformMatrix2x4fv,
            "uniformMatrix3x4fv":uniformMatrix3x4fv,
            "uniformMatrix4fv":uniformMatrix4fv
        };
    })(gl,onError,prog,vs,fs,header,footer,{});
}

function setTexture2dParams(gl,params) {
    params=params?params:{};

    if(params.mipmap) {
        gl.generateMipmap(gl.TEXTURE_2D);
    }

    var mag_filter=gl.LINEAR;
    var min_filter=gl.NEAREST_MIPMAP_LINEAR;

    var wrap_s=gl.REPEAT;
    var wrap_t=gl.REPEAT;


    if(params.mag_filter=="nearest") {
        mag_filter=gl.NEAREST
    }

    if(params.min_filter=="linear") {
        min_filter=gl.LINEAR;
    } else if(params.min_filter=="nearest") {
        min_filter=gl.NEAREST;
    } else if(params.min_filter=="nearest_mipmap_nearest") {
        min_filter=gl.NEAREST_MIPMAP_NEAREST;
    } else if(params.min_filter=="linear_mipmap_nearest") {
        min_filter=gl.LINEAR_MIPMAP_NEAREST;
    } else if(params.min_filter=="linear_mipmap_linear") {
        min_filter=gl.LINEAR_MIPMAP_LINEAR;
    }

    if(params.wrap_s=="clamp_to_edge") {
        wrap_s=gl.CLAMP_TO_EDGE;
    } else if(params.wrap_s=="mirrored_repeat") {
        wrap_s=gl.MIRRORED_REPEAT;
    }

    if(params.wrap_t=="clamp_to_edge") {
        wrap_t=gl.CLAMP_TO_EDGE;
    } else if(params.wrap_t=="mirrored_repeat") {
        wrap_t=gl.MIRRORED_REPEAT;
    }

    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,mag_filter);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,min_filter);

    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,wrap_s);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,wrap_t);
}

function createBind2dTexture4UI(gl,loc,data,w,h) {
    var tex=gl.createTexture();

    gl.activeTexture(gl.TEXTURE0+loc);
    gl.bindTexture(gl.TEXTURE_2D,tex);

    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32UI, w,h,0,gl.RGBA_INTEGER,gl.UNSIGNED_INT, data,0);

    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);

    return tex;
}

function createBind2dTexture1UI(gl,loc,data,w,h) {
    var tex=gl.createTexture();

    gl.activeTexture(gl.TEXTURE0+loc);
    gl.bindTexture(gl.TEXTURE_2D,tex);

    gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32UI, w,h,0,gl.RED_INTEGER,gl.UNSIGNED_INT, data,0);
    //gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32UI, w,h,0,gl.RED_INTEGER,gl.UNSIGNED_INT, null,0);
    //gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RED_INTEGER, gl.UNSIGNED_INT, data, 0);
    
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);

    return tex;
}


function createBind2dTextureData1UI(gl,loc,data) {
    //return new Promise(function(resolve, reject) {
        var maxTexSize=gl.getParameter(gl.MAX_TEXTURE_SIZE);
        
        var mesh=new Uint32Array(data);
        var paddedMesh=new Uint32Array(next_greater_power_of_2(mesh.length)); //pow2 padded
        paddedMesh.set(mesh);

        var meshTexWidth=Math.min(maxTexSize,paddedMesh.length);
        var meshTexHeight=paddedMesh.length/meshTexWidth;

        var tex=createBind2dTexture1UI(gl,loc,paddedMesh,meshTexWidth,meshTexHeight);
        console.log(mesh.length+":"+paddedMesh.length+":"+meshTexWidth +"x"+meshTexHeight);

        //resolve(tex);
        return tex;
    //});
}

function createBind2dTexture(gl,loc,img,params) {
    var tex=gl.createTexture();

    gl.activeTexture(gl.TEXTURE0+loc);
    gl.bindTexture(gl.TEXTURE_2D,tex);

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);

    setTexture2dParams(gl,params);

    return tex;
}

function next_greater_power_of_2(x) {
    return 2**(x-Math.min(x,1)).toString(2).length;
}

