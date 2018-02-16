
var createFreeLookCameraControl;

(function(){
    function vec3_dot(a,b) {
        return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
    }

    function vec3_length(v) {
        return Math.sqrt(vec3_dot(v,v));
    }

    function vec3_normal(out,v) {
        var l=1/vec3_length(v);
        out[0]=v[0]*l;
        out[1]=v[1]*l;
        out[2]=v[2]*l;
    }

    createFreeLookCameraControl=createFreeLookCameraControl||(function(input) {
        return (function(){
            var pos=[0,0,0];
            var pitch=0;
            var yaw=0;
            var velocity=[0,0,0];

            var wDown=false;
            var sDown=false;
            var aDown=false;
            var dDown=false;
            var spcDown=false;
            var ctrlDown=false;

            var posInterp=[0,0,0];
            var rotMat=[1,0,0, 0,1,0, 0,0,1];
            var viewMat=[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
            var quat=[0,0,0,1];

            var slow=0.92;
            var speed=0.01;
            var lookSpeed=0.005;
            
            if(input && input["pos"]) {
                pos[0]=input["pos"][0];
                pos[1]=input["pos"][1];
                pos[2]=input["pos"][2];
            }
            
            if(input && input["yaw"]) {
                yaw=input["yaw"];
            }
            if(input && input["pitch"]) {
                pitch=input["pitch"];
            }
            
            if(input && input["speed"]) {
                speed=input["speed"];
            }
            if(input && input["slow"]) {
                slow=input["slow"];
            }
            if(input && input["lookSpeed"]) {
                lookSpeed=input["lookSpeed"];
            }

            function onUpdate() {
                var sx=Math.sin(pitch);
                var sy=Math.sin(yaw);
                var cx=Math.cos(pitch);
                var cy=Math.cos(yaw);
                
                rotMat[0]=cy;
                rotMat[1]=0;
                rotMat[2]=-sy;
                rotMat[3]=sy*sx;
                rotMat[4]=cx;
                rotMat[5]=cy*sx;
                rotMat[6]=sy*cx;
                rotMat[7]=-sx;
                rotMat[8]=cy*cx;
                                
                viewMat[0]=rotMat[0];         
                viewMat[1]=rotMat[3]; 
                viewMat[2]=rotMat[6]; 
                
                viewMat[4]=rotMat[1]; 
                viewMat[5]=rotMat[4]; 
                viewMat[6]=rotMat[7]; 
                           
                viewMat[8]=rotMat[2]; 
                viewMat[9]=rotMat[5]; 
                viewMat[10]=rotMat[8];
            }

            function onStep(dt) {

                var right=[rotMat[0],0,rotMat[2]];
                var back=[rotMat[6],0,rotMat[8]];
                var up=[0,1,0];

                vec3_normal(right,right);
                vec3_normal(back,back);

                if(wDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=-back[i]*speed;}
                }

                if(sDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=back[i]*speed;}
                }

                if(aDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=-right[i]*speed;}
                }

                if(dDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=right[i]*speed;}
                }

                if(spcDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=up[i]*speed;}
                }

                if(ctrlDown) {
                    for(var i=0;i<3;i++) {velocity[i]+=-up[i]*speed;}
                }

                for(var i=0;i<3;i++) {
                    pos[i]+=velocity[i];
                    velocity[i]*=slow;
                }
            }

            function onRender(it) {
                for(var i=0;i<3;i++) {
                    posInterp[i]=pos[i]+velocity[i]*it;
                }
                
                viewMat[12]=-vec3_dot(posInterp,[rotMat[0],rotMat[1],rotMat[2]]);
                viewMat[13]=-vec3_dot(posInterp,[rotMat[3],rotMat[4],rotMat[5]]);
                viewMat[14]=-vec3_dot(posInterp,[rotMat[6],rotMat[7],rotMat[8]]);
                
                quat[3]=Math.sqrt(1+rotMat[0]+rotMat[4]+rotMat[8])/2;
                quat[0]=(rotMat[7]-rotMat[5])/(4*quat[3]);
                quat[1]=(rotMat[2]-rotMat[6])/(4*quat[3]);
                quat[2]=(rotMat[1]-rotMat[3])/(4*quat[3]);
            }

            function onKeyDown(event) {
                if(event.key=="w") {
                    wDown=true;
                } else if(event.key=="s") {
                    sDown=true;
                } else if(event.key=="a") {
                    aDown=true;
                } else if(event.key=="d") {
                    dDown=true;
                } else if(event.key=="e") {
                    spcDown=true;
                } else if(event.key=="q") {
                    ctrlDown=true;
                }
            }

            function onKeyUp(event) {
                if(event.key=="w") {
                    wDown=false;
                } else if(event.key=="s") {
                    sDown=false;
                } else if(event.key=="a") {
                    aDown=false;
                } else if(event.key=="d") {
                    dDown=false;
                } else if(event.key=="e") {
                    spcDown=false;
                } else if(event.key=="q") {
                    ctrlDown=false;
                }
            }

            function onMouseMove(event) {
                yaw-=event.movementX*lookSpeed;
                pitch-=event.movementY*lookSpeed;
                pitch=Math.min(Math.max(pitch,-1.57),1.57);
            }

            return {
                "update" : onUpdate,
                "step" : onStep,
                "render" : onRender,
                "keydown" : onKeyDown,
                "keyup" : onKeyUp,
                "mousemove" : onMouseMove,

                "getPos" : (function(){return posInterp.slice()}),
                "setPos" : (function(x,y,z){pos[0]=x;pos[1]=y;pos[2]=z;}),
                "getRot" : (function(){return rotMat.slice();}),
                "getQuat" : (function(){return quat.slice();}),

                "setSlow":(function(x){slow=x;}),
                "setSpeed":(function(x){speed=x;}),
                "setLookSpeed":(function(x){lookSpeed=x;}),

                "setPitch":(function(x){pitch=x;}),
                "getPitch" : (function(){return pitch;}),

                "setYaw":(function(x){yaw=x;}),
                "getYaw" : (function(){return yaw;}),
                
                "getView" :(function(){return viewMat.slice();}),
            };
        })();
    });
})();
