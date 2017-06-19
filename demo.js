var canvas,gl,root;
var barFps,barTime;
var prog,mouse,screenGeom;
var resScale=1.0;
var countFPS=createFpsCounter();
var startTime=Date.now();
var hasError=false;

function setErrorMsg(msg) {
    root.innerHTML=hasError?root.innerHTML:'';
    hasError=true;
    root.innerHTML+='<pre>'+msg+'</pre>';
}

function onAnimate() {
    if(hasError) {
        return false;
    }

    var width=Math.floor(canvas.offsetWidth*resScale);
    var height=Math.floor(canvas.offsetHeight*resScale);

    var difTime=Date.now()-startTime;

    if(difTime>=3.402823e+38) {
        startTime=Date.now();
        difTime=0;
    }

    var t=difTime/1000.0;
    var m=[mouse[0]*resScale,mouse[1]*resScale,mouse[2]*resScale,mouse[3]*resScale];

    //canvas.width=width;
    //canvas.height=height;

    prog.uniform3f("iResolution",width,height,0);
    prog.uniform1f("iGlobalTime",t);
    prog.uniform4f("iMouse",m[0],m[1],m[2],m[3]);

    screenGeom.draw(width,height);

    barFps.innerHTML = countFPS() + " fps";
    barTime.innerHTML = t.toFixed(2) ;

    requestAnimFrame(onAnimate);
}

function onLoad() {
    barTime=document.getElementById("barTime");
    barFps=document.getElementById("barFps");
    canvas=document.getElementById("canvas");
    root=document.getElementById("root");
    gl=createGLContext(canvas,{});

    canvas.onselectstart=null;

    if(!gl) {
        return;
    }

    var header="precision highp float;precision highp int;out vec4 outColor;"+
        "uniform vec3 iResolution;uniform float iGlobalTime;uniform vec4 iMouse;"+
        "uniform highp usampler2D iChannel0;";
    var footer="void main(){mainImage(outColor,gl_FragCoord.xy);}";

    if(!(prog=createProgram(gl,setErrorMsg,header,footer))){
        return;
    }

    prog.use();

    mouse=cursorInput(canvas);
    screenGeom=createScreenGeometry(gl);

    var maxTexSize=gl.getParameter(gl.MAX_TEXTURE_SIZE);

    var resources=[];
    resources.push(loadBinary("sibenik.dat").then(decompressLZMA));
    resources.push(loadText("demo.glsl"));
    
    Promise.all(resources).then((result)=>{
        var mesh=new Uint32Array(result[0]);
        var paddedMesh=new Uint32Array(next_greater_power_of_2(mesh.length)); //pow2 padded
        paddedMesh.set(mesh);

        var meshTexWidth=Math.min(maxTexSize,paddedMesh.length);
        var meshTexHeight=paddedMesh.length/meshTexWidth;

        createBind2dTexture1UI(gl,0,paddedMesh,meshTexWidth,meshTexHeight);
        console.log(mesh.length+":"+paddedMesh.length+":"+meshTexWidth +"x"+meshTexHeight);

        if(!prog.set(result[1])) {
            return;
        }

        prog.use();
        prog.uniform1i("iChannel0",0);
    });

    onAnimate();
}

window.onresize=(function(){window.scrollTo(0,0);});

window.requestAnimFrame =
    window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    window.oRequestAnimationFrame ||
    window.msRequestAnimationFrame ||
    (function(c,e){window.setTimeout(c,1000/60)});

window.onload = onLoad;

navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia;
