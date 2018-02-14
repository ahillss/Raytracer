
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

function createBind2dTexture(gl,loc,img) {
    var tex=gl.createTexture();

    gl.activeTexture(gl.TEXTURE0+loc);
    gl.bindTexture(gl.TEXTURE_2D,tex);

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);


    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);

    return tex;
}

function next_greater_power_of_2(x) {
    return 2**(x-Math.min(x,1)).toString(2).length;
}

